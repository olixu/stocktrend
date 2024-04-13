from nicegui import ui
from config import etf_codes
from data_utils import calculate_start_date, calculate_return_rates, format_return_rates, get_index_data, get_north_fund_flow_data, get_south_fund_flow_data, get_zt_pool_strong_data, get_zt_pool_previous_data, get_latest_trade_date
from format_utils import format_time, convert_columns_to_billions_and_round, dataframe_to_nicegui_table
from chart_utils import create_chart_options
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd
import schedule
import time
from threading import Thread
import asyncio

class HomePage:
    def __init__(self):
        self.end_date = get_latest_trade_date()
        self.return_rates = format_return_rates(calculate_return_rates(etf_codes, self.end_date))
        print("初始化完成")

    def create_header(self):
        with ui.header().style('background: #f3f5f8;') as header:
            with ui.row().classes('flex w-full items-center justify-start py-0 px-4').style('background: #f3f5f8;'):
                with ui.column().classes('items-center justify-center'):
                    ui.link('看盘号 KANPANHAO', '/').style(
                        'font-size: 2rem; font-weight: 500; text-decoration: underline; text-underline-offset: 8px; text-decoration-color: #f87171; text-decoration-thickness: 2px;text-align: left; line-height: 0.75')
                    ui.label('计划你的交易，交易你的计划').style(
                        'font-family: "KaiTi", "STKaiti", "仿宋", "FangSong", serif; font-size: 1rem; color: #333;text-align: left;')

                ui.space()

                ui.link('今日复盘', '/review').tailwind('flex-none', 'font-semibold', 'px-4', 'text-base', 'no-underline')
                ui.link('市场热点', '/market/focus').tailwind('flex-none', 'font-semibold', 'px-4', 'text-base', 'no-underline')

                with ui.dropdown_button('行业趋势', auto_close=True).classes(
                        'flex-none font-semibold px-4 text-base no-underline'):
                    with ui.list():
                        with ui.item(on_click=lambda: ui.notify('You clicked 行业跟踪')):
                            ui.link('行业跟踪', '/market/gz').tailwind('flex-none', 'font-semibold', 'px-4', 'text-base',
                                                                       'no-underline')
                        with ui.item(on_click=lambda: ui.notify('You clicked 行业分类')):
                            ui.link('行业分类', '/market/fl').tailwind('flex-none', 'font-semibold', 'px-4', 'text-base',
                                                                       'no-underline')

                ui.link('选股器', '/screener/bd').tailwind('flex-none', 'font-semibold', 'px-4', 'text-base', 'no-underline')

    def create_market_hotspots_grid(self):
        ui.label('市场热点').classes('text-xl font-bold my-3')
        with ui.grid(columns=2).classes(
                'grid gap-4 grid-cols-2 rounded-md shadow-md bg-white border border-blue-200 p-5 mb-3 w-[100%]'):
            self.create_index_trend_section()
            self.create_north_and_south_fund_flow_section()
            self.create_industry_etf_section()
            self.create_zt_pool_section()

    def create_index_trend_section(self):
        ui.label('指数趋势').classes('col-span-2 text-base font-semibold border-b-2 border-sky-700 pb-1')
        start_date = calculate_start_date(self.end_date, 365)
        index_shanghai_df = get_index_data("000001", start_date, self.end_date)
        index_shenzhen_df = get_index_data("399001", start_date, self.end_date)

        self.create_index_info_row(index_shanghai_df, '上证指数')
        self.create_index_info_row(index_shenzhen_df, '深圳成指')

        self.create_index_kline_chart(index_shanghai_df)
        self.create_index_kline_chart(index_shenzhen_df)

    def create_index_info_row(self, df, index_name):
        latest_close_price = df.iloc[-1]['收盘']
        today_change = (latest_close_price / df.iloc[-2]['收盘'] - 1) * 100
        change_class = 'text-green-700' if today_change < 0 else 'text-red-700'

        with ui.row():
            ui.label(index_name).classes('text-base font-semibold')
            ui.label(f'{latest_close_price}(').classes('pl-2 text-base font-semibold')
            ui.label(f'{today_change:+.2f}%').classes(f'{change_class} text-base font-semibold')
            ui.label(')').classes('text-base font-semibold')

        changes = {}
        for days in [5, 10, 20, 60, 120]:
            if len(df) >= days:
                past_price = df.iloc[-1 - days]['收盘']
                changes[f'{days}日涨跌幅'] = (latest_close_price / past_price - 1) * 100
            else:
                changes[f'{days}日涨跌幅'] = "数据不足"

        with ui.row().classes('gap-4 my-2 text-xs font-semibold'):
            for days in [5, 10, 20, 60, 120]:
                label_text = f'{days}日'
                change_text = f'{changes[f"{days}日涨跌幅"]:.2f}%' if isinstance(changes[f"{days}日涨跌幅"], float) else changes[
                    f"{days}日涨跌幅"]
                change_class = 'text-green-700' if changes[f"{days}日涨跌幅"] < 0 else 'text-red-700'
                ui.label(label_text).classes('underline underline-offset-4 mr-1')
                ui.label(change_text).classes(f'{change_class}')

    def create_index_kline_chart(self, df):
        kline_data = df[['开盘', '收盘', '最低', '最高']].values.tolist()
        options = {
            'grid': {
                'up': '0%',
                'left': '0%',
                'right': '10%',
                'bottom': '10%'
            },
            'xAxis': {
                'type': 'category',
                'data': df['日期'].tolist()
            },
            'yAxis': {
                'type': 'value',
                'scale': True,
                'show': True
            },
            'series': [{
                'name': 'K线',
                'type': 'candlestick',
                'data': kline_data
            }],
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross'
                }
            },
            'dataZoom': [
                {
                    'type': 'inside',
                    'start': 90,
                    'end': 100
                },
                {
                    'type': 'slider',
                    'start': 90,
                    'end': 100,
                    'handleSize': '80%',
                    'height': 40
                }
            ]
        }
        ui.echart(options=options).style('margin-top: -70px;')

    def create_north_and_south_fund_flow_section(self):
        ui.label('北向资金净买入(亿元)').classes('col-span-2 text-base font-semibold border-b-2 border-sky-700 pb-1')
        self.create_fund_flow_chart(get_north_fund_flow_data("沪股通"))

        ui.label('南向资金净买入(亿元)').classes('col-span-2 text-base font-semibold border-b-2 border-sky-700 pb-1')
        self.create_fund_flow_chart(get_south_fund_flow_data("沪股通"))

    def create_fund_flow_chart(self, df):
        df.value = df.value / 10000.0
        df['date'] = pd.to_datetime(df['date'])
        current_date = datetime.now()
        one_year_ago = current_date - timedelta(days=365)
        # 这里使用.copy()来创建一个df_filtered的实际副本
        df_filtered = df[(df['date'] >= one_year_ago) & (df['date'] <= current_date)].copy()
        df_filtered['date'] = df_filtered['date'].dt.strftime('%Y-%m-%d')
        colors = ['green' if value < 0 else 'red' for value in df_filtered['value'].tolist()]
        data_with_colors = [{'value': value, 'itemStyle': {'color': color}} for value, color in
                            zip(df_filtered['value'].tolist(), colors)]
        options = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'shadow'
                }
            },
            'xAxis': {
                'type': 'category',
                'data': df_filtered['date'].tolist()
            },
            'yAxis': {
                'type': 'value'
            },
            'series': [{
                'data': data_with_colors,
                'type': 'bar'
            }]
        }
        ui.echart(options=options).style('margin-top: -20px;').classes('col-span-2')

    def create_industry_etf_section(self):
        ui.label('行业ETF涨幅').classes('col-span-2 text-base font-semibold border-b-2 border-sky-700 pb-1')
        # 获取1日涨跌幅，并按照涨跌幅从高到低进行排序
        one_day_rates = self.return_rates["1日"]
        sorted_one_day_rates = sorted(one_day_rates.items(), key=lambda item: item[1], reverse=True)
        
        # 准备echarts所需的数据
        categories = [name for name, rate in sorted_one_day_rates]
        values = [rate for name, rate in sorted_one_day_rates]
        colors = ['red' if value > 0 else 'green' for value in values]
        options = {
        'grid': {
            'left': '3%',  # 减少左侧空白
            'right': '3%',  # 减少右侧空白
            'bottom': '10%',  # 为倾斜的x轴标签腾出空间
            'containLabel': True
        },
        'title': {
            'text': '单日涨跌幅(%)',
            'left': '0%',  # 将标题设置为靠左对齐
            'top': 10  # 调整标题距离顶部的距离
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'shadow'
            }
        },
        'xAxis': {
            'type': 'category',
            'data': categories,  # 假设categories已经定义
            'axisLabel': {
                'interval': 0,  # 显示所有标签
                'rotate': 45,  # 标签旋转45度
                'fontSize': 14,  # 调整字体大小以更好地适应标签
                'fontWeight': 'bold'  # 加粗标签
            }
        },
        'yAxis': {
            'type': 'value'
        },
        'series': [{
            'data': [
                {'value': value, 'itemStyle': {'color': color}}
                for value, color in zip(values, colors)  # 假设values和colors已经定义
            ],
            'type': 'bar',
            'label': {
                'show': True,  # 显示标签
                'position': 'top',  # 标签显示在柱子顶部
                'formatter': '{c}',  # 格式化标签，显示数值
                'fontSize': 14,  # 设置标签字体大小
                'fontWeight': 'bold',  # 标签字体加粗
                'color': 'black'  # 标签字体颜色
            }
        }]
    }
        ui.echart(options=options).style('margin-top: -20px;').classes('col-span-2').style('height: 400px')
    
        ui.label('行业ETF5/10/20/60日涨跌幅').classes('col-span-2 text-base font-semibold border-b-2 border-sky-700 pb-1')
        with ui.row().classes('col-span-2'):
            with ui.grid(columns=4).classes('grid gap-4 grid-cols-4 bg-white p-5 mb-3 w-[100%]'):
                values_5 = self.return_rates["5日"]
                sorted_one_day_rates = sorted(values_5.items(), key=lambda item: item[1], reverse=True)
                ui.echart(options=create_chart_options(sorted_one_day_rates, '涨跌幅5日(%)')).style('height: 800px')
                
                values_10 = self.return_rates["10日"]
                sorted_one_day_rates = sorted(values_10.items(), key=lambda item: item[1], reverse=True)
                ui.echart(options=create_chart_options(sorted_one_day_rates, '涨跌幅10日(%)')).style('height: 800px')
    
                values_20 = self.return_rates["20日"]
                sorted_one_day_rates = sorted(values_20.items(), key=lambda item: item[1], reverse=True)
                ui.echart(options=create_chart_options(sorted_one_day_rates, '涨跌幅20日(%)')).style('height: 800px')
    
                values_60 = self.return_rates["60日"]
                sorted_one_day_rates = sorted(values_60.items(), key=lambda item: item[1], reverse=True)
                ui.echart(options=create_chart_options(sorted_one_day_rates, '涨跌幅60日(%)')).style('height: 800px')

    def create_zt_pool_section(self):
        ui.label('涨停热点').classes('col-span-2 text-base font-semibold border-b-2 border-sky-700 pb-1')
        self.create_zt_pool_table(get_zt_pool_strong_data(self.end_date))

        ui.label('涨停股池').classes('col-span-2 text-base font-semibold border-b-2 border-sky-700 pb-1')
        self.create_zt_pool_table(get_zt_pool_previous_data(self.end_date))

    def create_zt_pool_table(self, df):
        columns, rows = dataframe_to_nicegui_table(df)
        table_height = '500px'
        ui.table(columns=columns, rows=rows, row_key='name').classes('col-span-2').style(
            f'height: {table_height}; overflow-y: auto;')

    def create_footer(self):
        with ui.footer(fixed=False).style('background-color: #f3f5f8'):
            with ui.column().classes('flex w-full items-center justify-start py-0 px-4').style('background: #f3f5f8;'):
                ui.label('Copyright ©2023 看盘号 stocktrend.top').style(
                    'font-family: "KaiTi"; font-size: 1rem; color: #333;text-align: left; line-height: 0.75')
                ui.label('洞悉数据，把握结构，跟随趋势，计划交易').style(
                    'font-family: "KaiTi"; font-size: 1rem; color: #333;text-align: left; line-height: 0.75')
                ui.label(
                    'STOCKTREND旨在传播更多市场信息，竭力但不保证信息的绝对准确、完整和及时性，仅供参考，不构成投资建议，据此操作，风险自担。问题及建议请发送邮件：kanpanhao@sina.com').style(
                    'font-family: "KaiTi"; font-size: 1rem; color: #333;text-align: left; line-height: 0.75')

    def run(self):
        print(50*'-')
        print("当前的时间为：", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ui.page_title('KANPANHAO-寻找策略之美')
        self.create_header()
        print("创建完header")
        self.create_market_hotspots_grid()
        print("创建完数据图")
        self.create_footer()
        print("创建完footer")
        ui.run()

if __name__ in {"__main__", "__mp_main__"}:
    home_page = HomePage()
    home_page.run()
    