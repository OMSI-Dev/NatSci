This is documentation for the M0 ADC sensor boards for Energy Transitions, custom within the firmware. Each of the three on-board hall sensors have been configured to specific polarity thresholds, as outlined below.


Sensor Index Mapping
Index	Sensor	Physical Position
0	S1	Middle
1	S2	Left
2	S3	Right


Sensor 0 — S1 (Middle)
Reading	Range (ADC counts)
South	< 1900 (enter) — stays South until > 2000
Neutral / Uncertain	1900 – 2500 (from rest)
North	> 2700 (enter) — stays North until < 2500

Sensor 1 — S2 (Left)
Reading	Range (ADC counts)
South	< 1650 (enter) — stays South until > 1950
Neutral / Uncertain	1650 – 2400 (from rest)
North	> 2550 (enter) — stays North until < 2400

Sensor 2 — S3 (Right)
Reading	Range (ADC counts)
South	< 1550 (enter) — stays South until > 1950
Neutral / Uncertain	1550 – 2400 (from rest)
North	> 2550 (enter) — stays North until < 2400
