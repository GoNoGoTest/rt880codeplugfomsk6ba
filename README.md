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
* **Channel name**: `R<band>-<network>-<district> <city> <call>` (e.g. `R2m-BR-6 Nacka SM0ABC`).
  * Band is derived from the `band` column or the output frequency (2 m or 70 cm today; other bands fall back to a rounded MHz label).
  * Network codes: BrandMeister→BR, Wires-X→WX, SvxReflector→SV, Echolink→EL, IRLP→IR, empty→FM, otherwise the uppercase value.
  * Rows with multiple networks are duplicated (one channel per network). If multiple `network_id` entries are present (slash-separated), they are appended to the matching channel name in order.
* **Access tones**
  * The first numeric value in `access` is used for both RX and TX tones; if none is found, `None` is written.
  * Tone values are suffixed with `Hz`.
* **Filtering**: rows with status `QRT` are skipped by default; include them with `--include-inactive`.
* **Sorting**: output channels are sorted by channel name (which now includes band and network) then frequency; numbering is sequential from 1.
* **Defaults**: analogue channel with High power, Wide bandwidth, Busy Lock=`Allow TX`, ANA TOT=`Off`, Tail Tone=`55Hz`, Scrambler=`Off`, DCS Type=`Normal` and mute code prefilled with zeros (see `DEFAULT_ROW` in `convert.py`).

## Examples

A small sample input and generated output live in `examples/`:

```bash
python convert.py examples/repeater_sample.csv examples/codeplug_sample.csv
```

## Open questions for full functionality

These answers are needed to close the remaining gaps and match the exact RT-880 expectations:

1. **Access / tones**
   * Today only the *first* numeric entry in `access` becomes both `RX TONE` and `TX TONE` (e.g. `1750 / 107.2` → `107.2Hz`).
   * Should 1750 Hz tone bursts, DTMF strings (e.g. `DTMF 3`), and multi-tone fields be mapped differently or split between RX/TX?
2. **Network IDs**
   * Currently appended to the channel name in order (first network → first ID, etc.).
   * Should they instead populate a dedicated field (e.g. `Contact`, `TG List`) or produce extra metadata files?
3. **Channel type and defaults**
   * All channels are written as analogue with fixed defaults (High power, Wide bandwidth, Busy Lock Allow TX, etc.).
   * Are there cases that must be digital/DMR, narrow bandwidth, or use different power/busy/TOT settings per row/band?
4. **Filtering**
   * Rows with status `QRT` are skipped unless `--include-inactive` is passed.
   * Are there other statuses or per-band rules that should filter or flag channels differently?
5. **Naming edge cases**
   * Band label logic currently knows 2 m and 70 cm; everything else becomes a rounded MHz label (e.g. `223.5` → `224M`).
   * Do you want explicit labels for 6 m, 10 m, 23 cm, or other ranges?
