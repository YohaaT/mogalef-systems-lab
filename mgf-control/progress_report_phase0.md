# progress_report_phase0

## resumen ejecutivo
Se creó la estructura canónica, se inventarió el lote inicial, se calcularon hashes SHA256, se detectaron duplicados exactos y se generó el catálogo maestro inicial.

## inventario por familia
- 99-unclassified: 13
- mgf-bands-lab: 2
- mgf-breakout-lab: 11
- mgf-divergence-lab: 5
- mgf-regime-filter-lab: 10
- mgf-risk-lab: 1
- mgf-stop-lab: 12

## duplicados detectados
- EL_ATR_Min_Max_v2.txt -> EL_ATR_Min_Max_v2
- EL_Indice_de_force_v2024.txt -> EL_Indice_de_force_v2024
- EL_Intelligent_Scalping_Target.txt -> EL_Intelligent_Scalping_Target
- EL_MACD_DIV (2).txt -> EL_MACD_DIV
- EL_MACD_DIV.txt -> EL_MACD_DIV
- EL_MOGALEF_Bands_2023_JM1.txt -> EL_MOGALEF_Bands_2023_JM1
- E_XLB_indicator.txt -> E_XLB_indicator
- E_XLB_signal.txt -> E_XLB_signal
- E_XLB_signal_directional.txt -> E_XLB_signal_directional

## variantes detectadas
- EL_Intelligent_Scalping_Target (base: EL_Stop_Intelligent)
- EL_MOGALEF_Bands_2023_JM1 (base: EL_MOGALEF_Bands)
- EL_MOGALEF_STOP (base: EL_MOGALEF_Bands)
- EL_Mogalef_Trend_Filter_V2 (base: EL_Mogalef_Trend_Filter)
- EL_NeutralZone_B_V2 (base: EL_NeutralZone)
- EL_Stop_Intel_v2_live (base: EL_Stop_Intelligent)
- EL_Stop_Intelligent_target (base: EL_Stop_Intelligent)
- E_XLB_signal_directional (base: E_XLB_signal)
- Super_Stop_Long_5beta (base: Super_Stop_Long)
- Super_Stop_Short_5beta (base: Super_Stop_Short)

## archivos enviados a revisión manual
- Webis serie 1.zip: zip archive requires manual review
- org.py: python helper script needs classification

## riesgos observados
- El archivo ZIP no se descomprimió en Fase 0 para mantener el alcance.
- org.py no se clasificó sin revisar su contenido.
- La clasificación actual de variantes se basa en nombre y no en comparación lógica profunda.

## siguiente acción recomendada
Ejecutar Fase 1 con specs funcionales de componentes prioritarios, respetando el límite de alcance por run.

Result:
Artifacts created: mgf-catalog/master_catalog.csv, mgf-catalog/family_map.yaml, mgf-catalog/duplicates_report.md, mgf-catalog/manual_review_queue.csv, mgf-control/inventory_summary.md, mgf-control/progress_report_phase0.md
Files read: PROJECT_MASTER.md, TOKEN_POLICY.md, RUN_PROTOCOL.md, raw_material/*
Scope respected: yes
Next recommended action: escribir la spec de un componente p0_core por run.
