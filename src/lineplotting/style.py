
OVERHEAD_VALUE_SIZE = 10
BARPLOTS_FIGURE_SIZE = (6, 4)
TIMESERIES_FIGURE_SIZE = (8, 2.1)
LEGEND_FONTSIZE = "medium"

line_marker = {
    "cpu": {
        "user.cpu.current": "x",
        "user.cpu.usage": "o",
        "structure.cpu.current": "x",
        "structure.cpu.usage": "o",
        "limit.cpu.lower": "v",
        "limit.cpu.upper": "^",
        "proc.cpu.user": "*",
        "proc.cpu.kernel": "*"},
    "mem": {
        "structure.mem.current": "x",
        "structure.mem.usage": "o",
        "limit.mem.lower": "v",
        "limit.mem.upper": "^",
        "proc.mem.resident": "o"},
    "disk": {
        "structure.disk.current": "x",
        "structure.disk.usage": "*",
        "limit.disk.lower": "v",
        "limit.disk.upper": "^",
        "proc.disk.writes.mb": "*",
        "proc.disk.reads.mb": "*"},
    "net": {
        "structure.net.current": "x",
        "structure.net.usage": "*",
        "limit.net.lower": "v",
        "limit.net.upper": "^",
        "proc.net.tcp.in.mb": "*",
        "proc.net.tcp.out.mb": "*"},
    "energy": {
        "structure.energy.max": "x",
        "structure.energy.usage": "o",
        "user.energy.max": "x",
        "user.energy.used": "o"
    }
}

dashes_dict = {"-": (1, 0), "--": (5, 7)}
line_style = {
    "cpu": {
        "user.cpu.usage": "-",
        "user.cpu.current": "-",
        "structure.cpu.current": "-",
        "structure.cpu.usage": "-",
        "limit.cpu.lower": "--",
        "limit.cpu.upper": "--",
        "proc.cpu.user": "-",
        "proc.cpu.kernel": "-"},
    "mem": {
        "structure.mem.current": "-",
        "structure.mem.usage": "-",
        "limit.mem.lower": "--",
        "limit.mem.upper": "--",
        "proc.mem.resident": "-"},
    "disk": {
        "structure.disk.current": "-",
        "structure.disk.usage": "-",
        "limit.disk.lower": "--",
        "limit.disk.upper": "--",
        "proc.disk.writes.mb": "-",
        "proc.disk.reads.mb": "-"},
    "net": {
        "structure.net.current": "-",
        "structure.net.usage": "-",
        "limit.net.lower": "--",
        "limit.net.upper": "--",
        "proc.net.tcp.in.mb": "-",
        "proc.net.tcp.out.mb": "-"},
    "energy": {
        "structure.energy.max": "-",
        "structure.energy.usage": "-",
        "user.energy.max": "-",
        "user.energy.used": "-"
    }
}