# --------------------------------------------------
#    Imports
# --------------------------------------------------
import os
import random
import pandas as pd
import time


# --------------------------------------------------
#    Data Functions
# --------------------------------------------------
def get_random_data(rows, cols):
    """ return a dataframe with random data

        Args:
            rows - number of rows int he dataframe
            cols - number of columns in the dataframe

        Returns:
            datafarme containing random data
    """
    data = []
    for _ in range(0, rows):
        r = []
        for _ in range(0, cols):
            r.append(random.randint(0, 1000))
        data.append(r)

    # convert to dataframe
    df = pd.DataFrame(data)

    # show process id to prove we are running in different processes
    df['pid'] = os.getpid()

    # pretend this takes a long time
    time.sleep(5)
    df['time'] = str(time.time())

    # success!
    return df
