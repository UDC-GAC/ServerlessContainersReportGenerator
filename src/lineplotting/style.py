OVERHEAD_VALUE_SIZE = 10

LEGEND_FONTSIZE = "medium"

LINE_MARK_EVERY = 15

line_marker = {
    "cpu": {
        "user.cpu.current": "x",
        "user.cpu.used": "o",
        "structure.cpu.current": "x",
        "structure.cpu.max": "x",
        "structure.cpu.used": "o",
        "limit.cpu.lower": "v",
        "limit.cpu.upper": "^",
        "proc.cpu.user": "*",
        "proc.cpu.kernel": "*"},
    "mem": {
        "structure.mem.current": "x",
        "structure.mem.used": "o",
        "limit.mem.lower": "v",
        "limit.mem.upper": "^",
        "proc.mem.resident": "o"
    },
    "accounting": {
        "user.accounting.coins": "x",
        "user.accounting.min_balance": "x",
        "user.accounting.max_debt": "x"
    },
    "tasks": {
        "bucket.tasks.input": "x",
        "bucket.tasks.processing": "x"
    },
    "energy": {
        "structure.energy.max": "x",
        "structure.energy.used": "o",
        "user.energy.max": "x",
        "user.energy.used": "o"
    }
}

dashes_dict = {"-": (1, 0), "--": (5, 7)}
line_style = {
    "cpu": {
        "user.cpu.used": "-",
        "user.cpu.current": "-",
        "structure.cpu.current": "-",
        "structure.cpu.max": "-",
        "structure.cpu.used": "-",
        "limit.cpu.lower": "--",
        "limit.cpu.upper": "--",
        "proc.cpu.user": "-",
        "proc.cpu.kernel": "-"
    },
    "mem": {
        "structure.mem.current": "-",
        "structure.mem.used": "-",
        "limit.mem.lower": "--",
        "limit.mem.upper": "--",
        "proc.mem.resident": "-"
    },
    "accounting": {
        "user.accounting.coins": "-",
        "user.accounting.max_debt": "-",
        "user.accounting.min_balance": "-"
    },
    "tasks": {
        "bucket.tasks.input": "-",
        "bucket.tasks.processing": "-"
    },
    "energy": {
        "structure.energy.max": "-",
        "structure.energy.used": "-",
        "user.energy.max": "-",
        "user.energy.used": "-"
    }
}
