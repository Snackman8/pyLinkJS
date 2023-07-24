""" business logic for example crud app """

# --------------------------------------------------
# Imports
# --------------------------------------------------
import pandas as pd


# --------------------------------------------------
# Functions
# --------------------------------------------------
def delete_record(props, pk):
    """ delete a record from the database

        Args:
            props - property bag allowing persistent storage for data variables    
            pk - primary key of the record to delete
     """        
    # replace with SQL call to delete from database
    
    # reload data from database
    
    # fake deletion for example
    df = props['df']
    pk = pd.Series([pk]).astype(df.index.dtype)[0]
    df = df.drop(pk)
    props['df'] = df


def get_record_count(props):
    """ return the number of records available

        Args:
            props - property bag allowing persistent storage for data variables    
    
        Returns:
            number of records in the data
     """
    # call SQL to determine

    # fake response
    df = props['df']
    return len(df)


def get_record_for_updating(props, pk):
    """ return a page of records for display
    
        Args:
            props - property bag allowing persistent storage for data variables    
            pk - primary key of the record to edit
        
        Returns:
            dictionary containing the information for the record
            {'primary_key': {'value': 5, 'dtype': 'int64'},
             'records': [{'field_name': 'first name', 'value': 'Bob', 'dtype': 'string'},
                         {'field_name': 'last_name', 'value': 'Smith', 'dtype': 'string'},
                         {'field_name': 'Amount', 'value': 100.23, 'dtype': 'Float64'},}
    """
    # thsi could be a call to SQL or reading from the stored dataframe
    df = props['df']
    pk = pd.Series([pk]).astype(df.index.dtype)[0]
    r = df.loc[pk]
    
    retval = {'primary_key': {'value': pk, 'dtype': df.index.dtype}}
    records = []
    for field_name in r.index:
        d = {}
        d['field_name'] = field_name
        d['value'] = r[field_name]
        d['dtype'] = str(df.dtypes[field_name])
        records.append(d)
    retval['records'] = records
    
    return retval
    

def get_records_for_display(props, starting_index, count):
    """ return a page of records for display
    
        Args:
            props - property bag allowing persistent storage for data variables    
            starting_index - index of the first row in the dataframe to be returned
            count - how many rows to return
        
        Returns:
            dataframe containing the data to display
    """
    # thsi could be a call to SQL or reading from the stored dataframe
    df = props['df']
    return df.iloc[starting_index:starting_index + count]


def init_data(props):
    """ initialize the database connection

        Args:
            props - property bag allowing persistent storage for data variables    
     """
    # replace with SQL call from database
    dtypes = {'first_name': 'string',
              'last_name': 'string',
              'prefix': 'string',
              'address': 'string',
              'company': 'string',
              'phone_number': 'string',}
    df = pd.read_csv('fake_data.csv.gz', index_col=0, parse_dates=['date', 'date_time'], dtype=dtypes)



    
    # rename any columns needed here
    # df = df.rename(columns={'a': 'b', 'c': 'd'}
    
    # drop any columns not needed for display
    # df = df.drop('col1', axis=1)
    
    # reorder the columns for display
    # df = df[['col1', 'col2', 'col3'])

    # save the dataframe to the props
    props['df'] = df


def resort_data(props, column_index):
    """ resort the data because the user clicked on a column header
    
        Args:
            props - property bag allowing persistent storage for data variables
            column_index - index of the column to sort by.  0 is the index, first data columns is 1
    """
    # get the dataframe
    df = props['df']
    
    if column_index == 0:
        df = df.sort_index()
    else:
        df = df.sort_values(df.columns[column_index - 1])
    
    props['df'] = df
    

def update_record(props, record_dict):
    """ update a record in the database

        Args:
            props - property bag allowing persistent storage for data variables
            record_dict - dictionary containing the information to update the record with.
                          See get_record_for_updating for format of this record_dict
    """
    
    # replace with SQL call to update from database
    
    # get the dataframe
    df = props['df']
    
    # update
    pk = record_dict['primary_key']['value']
    for d in record_dict['records']:
        # convert to the correct datatype
        converted_value = pd.Series([d['value']]).astype(d['dtype'])[0]
        df.loc[pk, d['field_name']] = converted_value 

    # save
    props['df'] = df
