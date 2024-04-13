def create_chart_options(data, title):
    categories = [item[0] for item in data]  # 获取类别名称
    values = [item[1] for item in data]  # 获取数值

    # 生成带有颜色和标签位置的数据点
    series_data = []
    for value in values:
        color = 'red' if value > 0 else 'green'
        label_position = 'right' if value > 0 else 'left'  # 根据值的正负设置标签位置
        data_point = {
            'value': value,
            'itemStyle': {
                'color': color
            },
            'label': {
                'show': True,
                'position': label_position,
                'color': 'black',
                'fontWeight': 'bold',
                'fontSize': 12
            }
        }
        series_data.append(data_point)

    return {
        'title': {
            'text': title,
            'left': 'center'
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'shadow'
            }
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '3%',
            'containLabel': True
        },
        'yAxis': {
            'type': 'category',
            'data': categories,
            'axisLabel': {
                'fontWeight': 'bold',
                'show': True  # 确保所有的yAxis名字都显示出来
            }
        },
        'xAxis': {
            'type': 'value',
            'position': 'top'
        },
        'series': [{
            'data': series_data,
            'type': 'bar',
            'barWidth': '60%'
        }]
    }