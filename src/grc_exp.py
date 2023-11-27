from src.common.config import OpenTSDBConfig, MongoDBConfig
from src.opentsdb import bdwatchdog
from TimestampsSnitch.src.mongodb.mongodb_agent import MongoDBTimestampAgent
import matplotlib.pyplot as plt
import numpy as np

def find_first_tuple_with_value(data, target_value):
    for timestamp, value in data:
        if value >= target_value:
            return timestamp, value
    return None  # If no matching tuple is found


def get_time_taken(data, value):
    match = find_first_tuple_with_value(data, value)
    time_sent = (value - 1) * 90
    time_transfered = match[0]
    return time_transfered - time_sent


bdw = bdwatchdog.BDWatchdog(OpenTSDBConfig())
mongoDBConfig = MongoDBConfig()
timestampingAgent = MongoDBTimestampAgent(mongoDBConfig.get_config_as_dict())

experiment_name = "GRC_EXP"
experiment = timestampingAgent.get_experiment(experiment_name, mongoDBConfig.get_username())
print(experiment)
start, end = experiment["start_time"], experiment["end_time"]
timeseries = bdw.get_timeseries("user0", start, end, [('user.accounting.coins', 'user')], downsample=5)["user.accounting.coins"]

# Convert the time stamps to times relative to 0 (basetime)
basetime = int(list(timeseries.keys())[0])
x = list(map(lambda point: int(point) - basetime, timeseries))
y = list(map(lambda point: int(point), timeseries.values()))

data = zip(x, y)

transactions_done = 275
sum = 0
times = list()
for n in range(1, transactions_done + 1):
    time_taken = get_time_taken(data, n)
    times.append(time_taken)
    sum += time_taken
    print("Value {0} took {1}".format(n, time_taken))

print("Average is {0}".format(int(sum / transactions_done)))

q1 = np.quantile(times, 0.25)
print(q1)
q2 = np.quantile(times, 0.50)
print(q2)
q3 = np.quantile(times, 0.75)
print(q3)
print(np.quantile(times, 0.90))

fig, axes = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(8, 2.9), gridspec_kw={'height_ratios': [1, 3]})

counts, bins = np.histogram(times, bins=40)
print(counts)
print(bins)
axes[1].hist(bins[:-1], bins, weights=counts)

axes[1].annotate(int(q1), xy=(q1, max(counts)+8), ha='center', fontsize=11)
axes[1].annotate(int(q2), xy=(q2, max(counts)+8), ha='center', fontsize=11)
axes[1].annotate(int(q3), xy=(q3, max(counts)+8), ha='center', fontsize=11)
axes[1].annotate("N={0}".format(transactions_done), xy=(max(times)-50, max(counts)+2), ha='center', fontsize=12)

axes[1].axvline(q1, color='red', alpha=.6, linewidth=2, linestyle="-.", ymax=0.92)
axes[1].axvline(q2, color='orange', alpha=.6, linewidth=2, linestyle="--", ymax=0.92)
axes[1].axvline(q3, color='green', alpha=.6, linewidth=2, linestyle="-", ymax=0.92)
axes[1].set_xlabel("Transaction time (s)", fontsize=12)
axes[1].set_ylabel("# Transactions", fontsize=12)
axes[1].spines[['right', 'top']].set_visible(False)
axes[1].set_ylim(0,60)

axes[0].boxplot(times, 0, vert=False, widths=0.15)
axes[0].get_yaxis().set_visible(False)
axes[0].axis('off')
axes[0].margins(y=-0.30)

plt.subplots_adjust(hspace=0)
fig.savefig("grc_transactions.png", bbox_inches='tight', pad_inches=0.01, format="png")
