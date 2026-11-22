# 烘邻共享灶 · 燃气偏差班报

烘邻社区厨房的用气交接工作台。值班人员登记用气与实际炉分钟，后台按班次收档计划将带证据的班报送到应用内模拟收件箱。

烘邻社区厨房有东厨、西厨和备餐间三个区域，轮班为 12 支社区烘焙与备餐小组提供灶台。模拟的上游是燃气表起止数与灶眼点火日志。值班员原先在各自的表格里记表差，厨房经理抄到交接群。忙班的总用量不能直接与空闲班比较，断档常被误算成连续超限，交接群重复转发也没有固定收档时刻。工作台统一炉时口径和班次证据，下游由厨房经理与运营观察员按回执号交接和导出。

## 页面与权限

| 角色 | 枚举 | 工作入口和权限 |
|---|---|---|
| 厨房经理周岚 | `manager` | 用气账登记班次和读数，发布按灶台和班别生效的新规则，查看队列、回执及导出 |
| 记录员林秋 | `recorder` | 用气账登记班次和读数，查看规则、队列、回执及导出 |
| 运营观察员许闻 | `observer` | 浏览台账、规则和队列，从模拟收件箱读取证据并导出 CSV |

| 账号 | 演示密码 |
|---|---|
| `manager@demo.local` | `HobShift#21` |
| `recorder@demo.local` | `HobShift#21` |
| `observer@demo.local` | `HobShift#21` |

## 值班剧本

1. 周岚在「分发规则」核对东侧烘焙灶 `H01` 晚班 V1。阈值 `1.500 m³/炉时`，连超 `2 格`，冷却 `45 分钟`，收档后 `8 分钟`送厨房值班箱。
2. 林秋在「用气账」打开 2026 年 11 月 20 日 17:00 至 18:00（上海时区）的 `HL-1120-E01`，核对该班的 4 次表差及炉分钟。
3. 17:15 时格登记 `0.900 m³ / 30 炉分钟`，17:30 时格登记 `1.200 m³ / 40 炉分钟`。两格强度均为 `1.800`，构成一次连续超限。
4. 模拟班次计划 18:08 投递。启动后 worker 会自动补齐历史到期班报和偏差提醒，收件箱显示实际处理时间。`HL-1120-E01` 冻结强度为 `3.340 × 60 ÷ 150 = 1.336 m³/炉时`。
5. 18:00 至 18:30 的 `HL-1120-E02` 也连超 2 格，计划 18:38 投递，仍处在 18:53 冷却边界内。该班有班报，偏差提醒显示冷却抑制。
6. 核对 `HL-1120-E03` 的缺测和恰好 `1.500` 的时格。两处都把连超归零。西侧 `HL-1120-W01` 第一个时格为 `0 m³ / 0 炉分钟`，判为无可评估读数。
7. 在「待发队列」查看 `HL-WEST-NEXT`。首次 seed 以启动时间安排一个约 125 分钟后的投递，已经登记 3 格。演示更短的实时流程时，可给当前灶台班别发布 V2，把收档延后设为 3 分钟，然后登记一个刚收档的班次并录入已结束时格。选用一段未被已有班次占用的时间。
8. 许闻打开「模拟收件箱」，按厨房值班箱筛选，下载 `receipt-<回执号>.csv`。规则改版后打开同一回执，仍可看到原版阈值、连续超限和逐格读数。

## 计算与投递口径

- 每个班次使用半开窗口 `[开班, 收档)`。以开班时刻为基点，每 15 分钟一格，末格可缩短。同灶台的班次窗口不可重叠。同一班次、时格只接收一笔读数。炉分钟是本格所有灶眼的实际点火分钟之和，受灶眼数和时格长度约束。
- 时格强度为 `用气量 × 60 ÷ 炉分钟`。班次强度为 `∑有效气量 × 60 ÷ ∑有效炉分钟`，由 Python `Decimal` 计算。严格大于阈值才计为超限，判定使用乘积精确比较。显示值四舍五入到 0.001。缺测、停炉、等于及低于阈值都会重置连续计数。无有效分母时强度留空。
- 经理发布的规则按「灶台、班别」递增版本。登记班次时绑定当前版本，并固化 `计划投递时刻 = 收档时间 + 延后分钟`。截止后读数被冻结。允许补登已收档班次，前提是计划投递仍在未来。
- worker 约每秒按数据库时间取一个或多个到期班次，依计划时间和班次 ID 顺序处理。每班发送一条班报。最长连超达到门槛时，使用同灶台、同班别上一条实际生成提醒的计划时刻加本班冷却时长作为边界，边界时刻允许下一条提醒。冷却抑制不刷新边界。
- 班次窗口自然键、收件箱 `(班次 ID, 消息类型)` 唯一约束、事务级调度锁共同保障重试和重复扫描。证据、回执、worker 产生的审计事件以及评估标记同事务提交。冻结的 JSON 证据包含规则、总量、有效覆盖、冷却边界和逐格结果。CSV 读取同一份冻结快照。

## 启动

```bash
cp .env.example .env
docker compose up --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

| 入口 | 地址 |
|---|---|
| 应用 | `http://127.0.0.1:18282` |
| API 文档 | `http://127.0.0.1:19282/docs` |
| PostgreSQL 16 | `127.0.0.1:17782` |

`SEED_DEMO=true` 启动时自动准备样本。手工运行 seed 可复核自然键和固定演示值。`.env` 的 `FRONTEND_PORT`、`BACKEND_PORT`、`DB_PORT` 和 `NETWORK_SUBNET` 控制宿主映射与子网，默认 `10.221.213.0/24`。`COMPOSE_PROJECT_NAME` 用于区分 Docker 资源，`DB_NAME`、`DB_USER`、`DB_PASSWORD` 和 `JWT_SECRET` 为本机开发配置。`docker compose down` 停止服务。确需清空本机演示数据时使用 `docker compose down -v`。

| 服务 | 层与技术 |
|---|---|
| `frontend` | Nginx、原生 HTML/CSS/JavaScript，转发 `/api/` |
| `backend` | Python 3.11、FastAPI、psycopg、JWT，接收业务操作及读取快照 |
| `worker` | Python 定时扫描 PostgreSQL，写入收件箱和共享健康心跳 |
| `db` | PostgreSQL 16，规则、班次、测量、回执与审计的持久化存储 |
| `redis` | Redis 7，队列页面的短期调度心跳与扫描统计 |

开发时在 `backend/` 安装 `requirements.txt`。连接本机已有 PostgreSQL 和 Redis 时，按环境指定 `DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`、`JWT_SECRET` 及 `REDIS_URL`，依次运行 `python -m scripts.migrate`、`python -m scripts.seed_demo`、`uvicorn src.main:app --port 8000`。另起终端通过 `WORKER_BEAT=./worker.beat python -m src.worker` 运行 worker。前端可通过 Compose Nginx 入口联调。批次端到端验收统一由 `scripts/verify-project.sh gb-5213` 启动并清理临时栈。

## 源码与枚举

- `backend/migrations/` 是 PostgreSQL 模型，`backend/scripts/` 管理启动、迁移及 seed。`backend/src/` 按 HTTP 路由和认证、业务服务、模型查询、输入 schema、中间件、常量与配置拆分。
- `frontend/src/` 按 API、状态、枚举、导航、页面、组件、表单事件和格式化逻辑拆分。表格、状态标记和空态跨页面复用。仪表在台账和回执共用。
- 枚举如下。后端常量在 `backend/src/constants/enums.py`，数据库约束在 `backend/migrations/001_initial.sql`，界面映射在 `frontend/src/constants/enums.js`。

| 枚举 | 值 | 使用位置 |
|---|---|---|
| 角色 | `manager`, `recorder`, `observer` | 账号 seed、会话认证、规则与台账写入权限、前端导航及表单 |
| 班别 | `morning`, `evening` | 规则与班次 schema、seed、台账、队列、收件箱 |
| 模拟收件箱 | `kitchen`, `operations` | 规则 schema、seed、scheduler、回执查询和导出、规则页与收件箱筛选 |
| 班报判定 | `alerted`, `cooldown`, `within_rule`, `unmeasurable` | Python 计算、worker 投递、队列和回执 UI |
| 时格状态 | `over`, `within`, `idle`, `missing` | Python 计算、冻结证据与 CSV、回执表格 |
| 消息类型 | `report`, `alert` | scheduler、回执查询和导出、收件箱和详情 |

## 使用边界

项目使用手工录入的模拟测量和应用内模拟投递，读数供用气交接与经营偏差复核。规则版本和完成后的记录长期留存。灶台名录与三个演示账号由 seed 管理。任务停止期间的到期班次会等 worker 恢复后补发，实际投递时间记录恢复后的处理时间。界面时间统一用上海时区，API 及导出保留时区偏移。

项目源码采用 [MIT](LICENSE)。附带字体采用各自的 SIL Open Font License，许可证位于 `frontend/src/fonts/`。
