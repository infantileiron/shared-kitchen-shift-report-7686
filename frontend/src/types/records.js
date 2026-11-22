/** @typedef {{id:number, code:string, label:string, area:string, burner_count:number}} Station */
/** @typedef {{id:number, role:'manager'|'recorder'|'observer', display_name:string, email:string}} Account */
/** Decimals arrive as strings. All timestamps carry a UTC offset. */
/** @typedef {{id:number, code:string, station_id:number, station_label:string, rule_version:number, due_at:string, starts_at:string, ends_at:string, evaluated_at:string|null, report_id:number|null}} Shift */
export {};
