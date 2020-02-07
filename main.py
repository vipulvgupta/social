import csv
import sys

# JEFF'S EXAMPLE, DO NOT EDIT

def example(input_file):
    counts = {}
    with open(input_file, "r") as f:
        reader = csv.reader(f, delimiter=",")

        # simple frequency count
        for row in reader:
            if row[3] not in counts:
                counts[row[3]] = 0
            counts[row[3]] += 1

    # normalize by max count
    normalized_counts = {}
    max_value = max(counts.values())
    for username in counts:
        normalized_counts[username] = counts[username] / max_value
    return normalized_counts

# -----------------------------------------
# PUT YOUR MEASURES AS FUNCTIONS BELOW HERE
# return a dict, where the key is the username and the value is the measure for the username
# see my example above
# please test it by hitting the run button above to check that it's outputting something that looks like the measure names (including yours) and a dict
# -----------------------------------------

def estimate_relationship_strength_via_typing_speed_and_reciprocity(csv_path):
    """
    This attempts to determine relationship strength based on a metric of
    "typing / thought speed". For each contact, it iterates through each
    message, calculates the time since the last message and measures the
    length of the message, and then scales the length by a factor of the time
    in order to determine how fast the message was typed in relation to the
    previous message. The metric removes outliers and attempts to account for
    gaps in time, implying a new thread of conversation.

    We purposely don't adjust for "sent" / "recieved" _within the thought
    speed metric_ (though we do it elsewhere) since we guess within a close
    relationship this metric would apply to both parties, and also this allows
    us to measure one person's response time to a given message sent by the
    other party.

    That said, we do have a bit of adjustment and shifting based on a simple
    ratio of sent / recieved text counts, with the underlying intuition being
    that one might be closer to a person who also has a higher degree of
    reciprocity in terms of the amount of total typing / text sent.

    The hypothesis motivating this metric is that people who are closer to each
    other might feel less compelled to spend more time thinking about the
    contact of their messages (as opposed to someone you're less familiar with,
    who you might spend more time writing to).
    """

    # Import statements:
    from collections import defaultdict
    import csv
    import datetime
    import statistics
    import math

    # CSV column index constants:
    TIMESTAMP     = 0
    SENT_RECIEVED = 1
    MESSAGE       = 2
    PERSON        = 3
    TYPE          = 4

    # Read data from CSV:
    contact_data = defaultdict(lambda: [])
    with open(csv_path) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            parsed_time = datetime.datetime.strptime(
                row[TIMESTAMP], "%Y-%m-%d %H:%M:%S+00:00")
            contact_data[row[PERSON]].append({
                "time":     parsed_time,
                "was_sent": row[SENT_RECIEVED] == "sent",
                "length":   len(row[MESSAGE]),
                "type":     row[TYPE]
            })

    # Iterate over each contact:
    results = {}
    for contact in contact_data.keys():
        # Sort messages in the order of timestamp, increasing:
        messages = contact_data[contact]
        messages.sort(key=lambda x: x["time"])

        # Calculate a measure of sent vs. recieved. The intuition here is that
        # closer relationships would have higher degree of reciprocity between
        # message sending; we can also use this to adjust a bit the measure of
        # "typing / thought" speed since that main measure does not distinguish
        # between sent or recieved messages.
        sent_count  = 1
        total_count = 1
        for msg in messages:
            if msg["was_sent"]:
                sent_count += msg["length"]
            total_count += msg["length"]

        # Calculate the final sent vs. recieved differential metric. The 0.03
        # subtracted from the end is meant to represent a bit of leeway in terms
        # of what would be considered an "acceptable" sent vs. recieved ratio
        # for a close relationship (in essence, anything above 0.47 or below
        # 0.53 would result in a negative `sent_diff` value) and then allows us
        # to "reward" certain relationship strength values if they produce
        # negative `sent_diff` values, as we're subtracting `sent_diff` from
        # our later "typing / thought" speed metric.
        sent_diff = ((abs(0.5 - (sent_count / total_count)) / 2) ** 1.5) - 0.03

        # Calculate a measure of "typing / thought" speed:
        speeds = []
        for i in range(1, len(messages)):
            a = messages[i]
            b = messages[i - 1]

            # Calculate time since the last message:
            time_since_last = max((a["time"] - b["time"]).total_seconds(), 0.5)

            # Remove breaks longer than 4 hours to account for different
            # conversation topics, on unread:
            MAX_SECONDS = 60 * 60 * 4
            if time_since_last > MAX_SECONDS:
                continue

            # Calculate a metric of "type speed" based on length and time since
            # the previous message:
            msg_length = b["length"]
            type_speed = msg_length / (time_since_last ** 2.5)
            speeds.append(type_speed)

        # Adjust for outliers (using a simple standard deviation test):
        if len(speeds) > 5:
            mean                = statistics.mean(speeds)
            stdev               = statistics.stdev(speeds)
            adjusted_speeds     = [x for x in speeds if (x > mean - 2 * stdev)]
            adjusted_speeds     = [x for x in adjusted_speeds if (x < mean + 2 * stdev)]
            avg_adjusted_speeds = statistics.mean(adjusted_speeds)

            # Do some exponential decay (increasing form) to scale number
            # between 0 and 1 and to motivate idea of that increasing
            # conversation speed will rise friendships faster than otherwise.
            # The 1.76 coefficient was determined through trial-and-error.
            exp_adjusted_speeds = (1 - math.exp(-avg_adjusted_speeds * 1.76))

            # Store final result, with an adjustment based on the sent /
            # recieved differential metric calculated above:
            results[contact] = min(max(exp_adjusted_speeds - sent_diff, 0), 1)
        else:
            # Zero value if not enough data found:
            results[contact] = 0

    return results



# ----------------------------------------
# DON'T EDIT BELOW HERE
# THIS RUNS ALL THE FUNCTIONS IN THIS FILE
# ----------------------------------------

this_module = sys.modules[__name__]
for attribute in dir(this_module):
  measure = getattr(this_module, attribute)
  if callable(measure):
    print(attribute, measure('example.csv'))
# note the example.csv is a fake example, so I wouldn't use that output for anything important