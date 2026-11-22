/** @typedef {{id:number, code:string, label:string, area:string, burner_count:number}} Station */
/** @typedef {{id:number, role:'manager'|'recorder'|'observer', display_name:string, email:string}} Account */
/** Decimals arrive as strings. All timestamps carry a UTC offset. */
/** @typedef {{id:number, code:string, station_id:number, station_label:string, rule_version:number, due_at:string, starts_at:string, ends_at:string, evaluated_at:string|null, report_id:number|null}} Shift */
/** @typedef {{id:number, shift_id:number, shift_code:string, previous_outcome:string, revised_outcome:string, reason:'readings_backfilled'|'cooldown_boundary', detail:object, source_version:number, finished_at:string}} Revision */
export {};
