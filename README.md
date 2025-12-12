# rt880codeplugfomsk6ba

Script to generate codeplugs för Radtel RT-880 from repeater list on https://sk6ba.se/vhf/repeater/karta/

## Usage

```bash
python convert.py path/to/repeater_list.csv path/to/output_codeplug.csv
```

* Input: semicolon-separated CSV with comma as decimal separator (as exported from the Swedish repeater list).
* Output: comma-separated CSV with dot decimal that matches the RT-880 codeplug format.

## Rules implemented

* **Frequencies**
  * `Rx Frequency` = `output` from source.
  * `Tx Frequency` = `output + tx_shift` (simplex if no shift).
  * Frequencies are written with 5 decimal places.
* **Channel name**: `R<band>-<network>-<district> <city> <call>` (e.g. `R2M-BR-6 Nacka SM0ABC`).
  * City is truncated at the first space (e.g. `Oslo / Heggedal` → `Oslo`).
  * Call is truncated to the bare callsign before whitespace, parentheses, or slash suffixes (e.g. `SK6QW/R (353113)` → `SK6QW`).
  * Band is derived from the `band` column or the output frequency with explicit labels: 2M, 70C, 6M, 23C. Other ranges fall back to a rounded MHz label.
  * Network codes: BrandMeister→BR, Wires-X→WX, SvxReflector→SV, Echolink→EL, IRLP→IR, empty→FM, otherwise the uppercase value.
  * Rows with multiple networks are duplicated (one channel per network). If multiple `network_id` entries are present (slash-separated), they are appended to the matching channel name in order.
* **Access tones**
  * RX tone is always blank.
  * TX tone is the first numeric CTCSS value (40–300 Hz) found in `access` (e.g. `1750 / 107.2` → `107.2Hz`). Tone bursts (e.g. 1750) and DTMF are ignored.
* **Filtering**: rows with status other than `QRV` are skipped by default; include everything with `--include-inactive`.
* **Sorting**: output channels are sorted by channel name (which now includes band and network) then frequency; numbering is sequential from 1.
* **Defaults**: analogue channel with High power, Wide bandwidth, Busy Lock=`Allow TX`, ANA TOT=`Off`, Tail Tone=`55Hz`, Scrambler=`Off`, DCS Type=`Normal` and mute code prefilled with zeros (see `DEFAULT_ROW` in `convert.py`).

## Examples

A small sample input and generated output live in `examples/`:

```bash
python convert.py examples/repeater_sample.csv examples/codeplug_sample.csv
```

## Current scope

* Analogue-only output with the defaults above.
* Network IDs are appended to the channel name (e.g. `R70C-EL-2 ... (27796)`).
* DTMF and other non-CTCSS signalling are ignored in v1.

## v1 readiness checklist

The script currently covers everything needed for the initial analogue workflow:

* QRV filtering with an opt-out flag.
* Explicit band labels (2M/70C/6M/23C) derived from the `band` column or output frequency.
* Multi-network splitting with matching `network_id` association and naming.
* CTCSS handling that populates TX tone only when a numeric 40–300 Hz tone is present; RX tone is always blank.
* Dot-decimal, comma-separated output with sequential channel numbering and the RT-880 column layout.

Planned for a later version: DMR/TG mapping and richer handling of DTMF or other signalling beyond CTCSS.
