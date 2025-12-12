"""Convert repeater CSV to RT-880 codeplug CSV.

Usage:
    python convert.py input.csv output.csv

The input repeater list is expected to be semicolon-separated with comma
as decimal separator. Output uses comma separator and decimal point.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

# Mapping of network names to the short codes used in the channel name.
NETWORK_CODES = {
    "brandmeister": "BR",
    "brandmeister bm": "BR",
    "bm": "BR",
    "wires-x": "WX",
    "wiresx": "WX",
    "svxreflector": "SV",
    "svx reflector": "SV",
    "echolink": "EL",
    "irlp": "IR",
    "fm": "FM",
}

# Column order for the generated codeplug.
OUTPUT_HEADER = [
    "Channel Number",
    "Rx Frequency",
    "Tx Frequency",
    "Channel Type",
    "Power",
    "Scan Add",
    "Channel Name",
    "TG List",
    "Contact",
    "DMR Enrcypt",
    "DMR Mode",
    "Timeslot",
    "Colour Code",
    "DMR Politely TX",
    "DMR TOT",
    "Promiscuos Mode",
    "Channel ID",
    "ID Select",
    "RX TONE",
    "TX TONE",
    "Bandwidth (kHz)",
    "Busy Lock",
    "ANA TOT",
    "Tail Tone",
    "Scrambler",
    "DCS Type",
    "ANA Mute Code 1",
    "ANA Mute Code 2",
    "ANA Mute Code 3",
    "AM_FM RX",
    "RX_TX Limit",
]

DEFAULT_ROW = {
    "Channel Type": "Analogue",
    "Power": "High",
    "Scan Add": "Add",
    "TG List": "",
    "Contact": "",
    "DMR Enrcypt": "",
    "DMR Mode": "",
    "Timeslot": "",
    "Colour Code": "",
    "DMR Politely TX": "",
    "DMR TOT": "",
    "Promiscuos Mode": "",
    "Channel ID": "",
    "ID Select": "",
    "Bandwidth (kHz)": "Wide",
    "Busy Lock": "Allow TX",
    "ANA TOT": "Off",
    "Tail Tone": "55Hz",
    "Scrambler": "Off",
    "DCS Type": "Normal",
    "ANA Mute Code 1": "000000000000000000000000",
    "ANA Mute Code 2": "",
    "ANA Mute Code 3": "",
    "AM_FM RX": "FM",
    "RX_TX Limit": "RX",
}


@dataclass
class SourceRow:
    data: dict

    @property
    def status(self) -> str:
        return (self.data.get("status") or "").strip()

    @property
    def output_freq(self) -> Optional[float]:
        raw = self.data.get("output", "")
        return _to_float(raw)

    @property
    def tx_shift(self) -> float:
        raw = self.data.get("tx_shift", "")
        return _to_float(raw) or 0.0

    @property
    def networks(self) -> List[str]:
        return _split_multi(self.data.get("network")) or [""]

    @property
    def network_ids(self) -> List[str]:
        return _split_multi(self.data.get("network_id"))

    @property
    def district(self) -> str:
        return (self.data.get("district") or "").strip()

    @property
    def city(self) -> str:
        return (self.data.get("city") or "").strip()

    @property
    def call(self) -> str:
        return (self.data.get("call") or "").strip()

    @property
    def access(self) -> str:
        return (self.data.get("access") or "").strip()


@dataclass
class Channel:
    rx_frequency: float
    tx_frequency: float
    channel_name: str
    rx_tone: str
    tx_tone: str


def _split_multi(value: Optional[str]) -> List[str]:
    if not value:
        return []
    parts = [p.strip() for p in value.split("/")]
    return [p for p in parts if p]


def _to_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_ctcss(access: str) -> str:
    """Return the first numeric CTCSS tone in Hz, or blank if none is found."""

    candidates = _split_multi(access.replace(" ", "")) if access else []
    if not candidates:
        candidates = access.replace(" ", "").replace("/", " ").split() if access else []

    for candidate in candidates:
        value = _to_float(candidate)
        if value is None:
            continue
        if 40.0 <= value <= 300.0:
            text = ("{:.1f}".format(value)).rstrip("0").rstrip(".")
            return f"{text}Hz"
    return ""


def network_code(raw: str) -> str:
    key = raw.strip().lower()
    return NETWORK_CODES.get(key, "FM" if not key else key.upper())


def _short_city(city: str) -> str:
    city = city.strip()
    if not city:
        return ""
    return city.split()[0]


def _base_callsign(call: str) -> str:
    call = call.strip()
    if not call:
        return ""
    # Drop everything after the first whitespace or parenthesis
    call = call.split()[0].split("(")[0].strip()
    # Keep only the part before any slash suffix (e.g. "/R")
    if "/" in call:
        call = call.split("/")[0]
    return call


def build_channel_name(net: str, row: SourceRow) -> str:
    code = network_code(net)
    band = band_label(row)
    prefix_parts = [f"R{band}", code]
    if row.district:
        prefix_parts.append(row.district)
    prefix = "-".join(prefix_parts)
    city = _short_city(row.city)
    call = _base_callsign(row.call)
    suffix_parts = [city, call]
    suffix = " ".join([p for p in suffix_parts if p]).strip()
    return prefix if not suffix else f"{prefix} {suffix}"


def band_label(row: SourceRow) -> str:
    """Return a short band label like 2m or 70cm for the channel name."""

    raw_band = (row.data.get("band") or "").strip().lower()
    if raw_band in {"2", "2m", "144"}:
        return "2M"
    if raw_band in {"70", "70cm", "430"}:
        return "70C"
    if raw_band in {"6", "6m", "50"}:
        return "6M"
    if raw_band in {"23", "23cm", "1200"}:
        return "23C"

    freq = row.output_freq or 0.0
    if 50 <= freq < 55:
        return "6M"
    if 140 <= freq < 150:
        return "2M"
    if 420 <= freq < 471:
        return "70C"
    if 1240 <= freq < 1320:
        return "23C"

    if freq:
        rounded = int(round(freq))
        return f"{rounded}M"
    return "FM"


def generate_channels(rows: Iterable[SourceRow], include_inactive: bool = False) -> List[Channel]:
    channels: List[Channel] = []
    for row in rows:
        is_active = row.status.upper() == "QRV"
        if not include_inactive and not is_active:
            continue
        rx = row.output_freq
        if rx is None:
            continue
        tx = rx + row.tx_shift
        tx_tone = parse_ctcss(row.access)

        nets = row.networks
        ids = row.network_ids
        for idx, net in enumerate(nets):
            name = build_channel_name(net, row)
            if idx < len(ids) and ids[idx]:
                name = f"{name} ({ids[idx]})"
            channels.append(
                Channel(
                    rx_frequency=rx,
                    tx_frequency=tx,
                    channel_name=name,
                    rx_tone="",
                    tx_tone=tx_tone,
                )
            )
    channels.sort(key=lambda ch: (ch.channel_name, ch.rx_frequency))
    return channels


def format_frequency(value: float) -> str:
    return f"{value:.5f}"


def write_output(channels: List[Channel], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADER, delimiter=",")
        writer.writeheader()
        for idx, ch in enumerate(channels, start=1):
            row = {**DEFAULT_ROW}
            row.update(
                {
                    "Channel Number": idx,
                    "Rx Frequency": format_frequency(ch.rx_frequency),
                    "Tx Frequency": format_frequency(ch.tx_frequency),
                    "Channel Name": ch.channel_name.strip(),
                    "RX TONE": ch.rx_tone,
                    "TX TONE": ch.tx_tone,
                }
            )
            writer.writerow(row)


def read_source(path: Path) -> List[SourceRow]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        return [SourceRow({k: (v or "") for k, v in row.items()}) for row in reader]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert repeater list to RT-880 codeplug CSV")
    parser.add_argument("input", type=Path, help="Path to the semicolon-separated repeater CSV")
    parser.add_argument("output", type=Path, help="Path to write the RT-880 codeplug CSV")
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include rows with status QRT (inactive). By default they are skipped.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_source(args.input)
    channels = generate_channels(rows, include_inactive=args.include_inactive)
    write_output(channels, args.output)


if __name__ == "__main__":
    main()
