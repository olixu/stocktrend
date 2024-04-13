def format_time(df, column_name):
    # 检查指定列是否在DataFrame中
    if column_name in df.columns:
        # 使用字符串格式化转换时间
        df[column_name] = df[column_name].apply(lambda x: '{:0>6}'.format(x))  # 确保是6位数字
        df[column_name] = df[column_name].str.slice(0, 2) + ':' + \
                          df[column_name].str.slice(2, 4) + ':' + \
                          df[column_name].str.slice(4, 6)
    return df

def convert_columns_to_billions_and_round(df, columns_to_convert):
    billion = 10**8
    # 先将整个DataFrame保留小数点后两位
    df = df.round(2)
    # 调用函数格式化'昨日封板时间'列
    df = format_time(df, '昨日封板时间')
    for column in columns_to_convert:
        if column in df.columns:
            # 将指定列的数值除以10^8
            df[column] = (df[column] / billion).round(2)
            # 更新列名以反映单位变化
            df.rename(columns={column: f"{column}(亿)"}, inplace=True)
    return df

def dataframe_to_nicegui_table(df):
    # 指定要转换的列名
    columns_to_convert = ['成交额', '流通市值', '总市值']
    # 转换指定列并保留小数点后两位
    df = convert_columns_to_billions_and_round(df, columns_to_convert)
    
    # 创建NiceGUI的columns
    columns = [{'name': col, 'label': col, 'field': col, 'sortable': True} for col in df.columns]
    
    # 创建NiceGUI的rows
    rows = df.to_dict('records')
    
    return columns, rows