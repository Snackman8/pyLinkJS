# --------------------------------------------------
#    Imports
# --------------------------------------------------
import random
import pandas as pd


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
    
    # success!
    return df
