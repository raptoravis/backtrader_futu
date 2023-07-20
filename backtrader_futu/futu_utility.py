import logging
from functools import lru_cache
from termcolor import colored
from enum import Enum
import futu as ft
from typing import Callable, List, Dict, Optional, Type, Tuple
from .object import ContractData, Exchange
from .utility import load_json, save_json, get_folder_path


# 交易所映射
EXCHANGE_VT2FUTU: Dict[Exchange, str] = {
    Exchange.SMART: "US",
    Exchange.SEHK: "HK",
    Exchange.SSE: "SH",
    Exchange.SZSE: "SZ",
}
EXCHANGE_FUTU2VT: Dict[str, Exchange] = {v: k for k, v in EXCHANGE_VT2FUTU.items()}


class EMarket(Enum):
    HK = "HK"
    US = "US"
    SH = "SH"
    SZ = "SZ"


class ESimple(Enum):
    NONE = ft.StockField.NONE
    CUR_PRICE = ft.StockField.CUR_PRICE  # 最新价 例如填写[10,20]值区间
    # (现价 ft.StockField.# (- 52周最高)/52周最高，对应PC端离52周高点百分比 例如填写[-30,-10]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%，如20实际对应20%）
    CUR_PRICE_TO_HIGHEST52_WEEKS_RATIO = ft.StockField.CUR_PRICE_TO_HIGHEST52_WEEKS_RATIO
    # (现价 ft.StockField.# (- 52周最低)/52周最低，对应PC端离52周低点百分比 例如填写[20,40]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    CUR_PRICE_TO_LOWEST52_WEEKS_RATIO = ft.StockField.CUR_PRICE_TO_LOWEST52_WEEKS_RATIO
    # (今日最ft.StockField.# (高 - 52周最高)/52周最高 例如填写[-3,-1]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    HIGH_PRICE_TO_HIGHEST52_WEEKS_RATIO = ft.StockField.HIGH_PRICE_TO_HIGHEST52_WEEKS_RATIO
    # (今日最ft.StockField.# (低 - 52周最低)/52周最低 例如填写[10,70]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    LOW_PRICE_TO_LOWEST52_WEEKS_RATIO = ft.StockField.LOW_PRICE_TO_LOWEST52_WEEKS_RATIO
    VOLUME_RATIO = ft.StockField.VOLUME_RATIO  # 量比 例如填写[0.5,30]值区间
    BID_ASK_RATIO = ft.StockField.BID_ASK_RATIO  # 委比 例如填写[-20,80.5]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    LOT_PRICE = ft.StockField.LOT_PRICE  # 每手价格 例如填写[40,100]值区间
    # 市值 例如ft.StockField.# 市值填写[50000000,3000000000]值区间
    MARKET_VAL = ft.StockField.MARKET_VAL
    # 市盈率 (ft.StockField.静# 市盈率态) 例如填写[-8,65.3]值区间
    PE_ANNUAL = ft.StockField.PE_ANNUAL
    # 市盈率TTMft.StockField.# 市盈率 例如填写[-10,20.5]值区间
    PE_TTM = ft.StockField.PE_TTM
    PB_RATE = ft.StockField.PB_RATE  # 市净率 例如填写[0.5,20]值区间
    CHANGE_RATE_5MIN = ft.StockField.CHANGE_RATE_5MIN  # 五分钟价格涨跌幅 例如填写[-5,6.3]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    CHANGE_RATE_BEGIN_YEAR = (
        ft.StockField.CHANGE_RATE_BEGIN_YEAR
    )  # 年初至今价格涨跌幅 例如填写[-50.1,400.7]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    PS_TTM = ft.StockField.PS_TTM  # 市销率(TTM) 例如填写 [100, 500] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    PCF_TTM = ft.StockField.PCF_TTM  # 市现率(TTM) 例如填写 [100, 1000] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    TOTAL_SHARE = ft.StockField.TOTAL_SHARE  # 总股数 例如填写 [1000000000,1000000000] 值区间 (单位：股)
    FLOAT_SHARE = ft.StockField.FLOAT_SHARE  # 流通股数 例如填写 [1000000000,1000000000] 值区间 (单位：股)
    FLOAT_MARKET_VAL = ft.StockField.FLOAT_MARKET_VAL  # 流通市值 例如填写 [1000000000,1000000000] 值区间 (单位：元)


class EAccumulate(Enum):
    NONE = ft.StockField.NONE
    CHANGE_RATE = ft.StockField.CHANGE_RATE  # 涨跌幅 例如填写[-10.2,20.4]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    AMPLITUDE = ft.StockField.AMPLITUDE  # 振幅 例如填写[0.5,20.6]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    VOLUME = ft.StockField.VOLUME  # 日均成交量 例如填写[2000,70000]值区间
    TURNOVER = ft.StockField.TURNOVER  # 日均成交额 例如填写[1400,890000]值区间
    TURNOVER_RATE = ft.StockField.TURNOVER_RATE  # 换手率 例如填写[2,30]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）


class EFinancial(Enum):
    NONE = ft.StockField.NONE
    NET_PROFIT = "NET_PROFIT"  # 净利润 例如填写[100000000,2500000000]值区间
    NET_PROFIX_GROWTH = "NET_PROFIX_GROWTH"  # 净利润增长率 例如填写[-10,300]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    SUM_OF_BUSINESS = "SUM_OF_BUSINESS"  # 营业收入 例如填写[100000000,6400000000]值区间
    SUM_OF_BUSINESS_GROWTH = "SUM_OF_BUSINESS_GROWTH"  # 营收同比增长率 例如填写[-5,200]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    NET_PROFIT_RATE = "NET_PROFIT_RATE"  # 净利率 例如填写[10,113]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    GROSS_PROFIT_RATE = "GROSS_PROFIT_RATE"  # 毛利率 例如填写[4,65]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    DEBT_ASSET_RATE = "DEBT_ASSET_RATE"  # 资产负债率 例如填写[5,470]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    RETURN_ON_EQUITY_RATE = "RETURN_ON_EQUITY_RATE"  # 净资产收益率 例如填写[20,230]值区间（该字段为百分比字段，默认不展示%，如20实际对应20%）
    ROIC = "ROIC"  # 盈利能力属性投入资本回报率 例如填写 [1.0,10.0] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    ROA_TTM = "ROA_TTM"  # 资产回报率(TTM) 例如填写 [1.0,10.0] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%。仅适用于年报。）
    EBIT_TTM = "EBIT_TTM"  # 息税前利润(TTM) 例如填写 [1000000000,1000000000] 值区间（单位：元。仅适用于年报。）
    EBITDA = "EBITDA"  # 税息折旧及摊销前利润 例如填写 [1000000000,1000000000] 值区间（单位：元）
    OPERATING_MARGIN_TTM = "OPERATING_MARGIN_TTM"  # 营业利润率(TTM) 例如填写 [1.0,10.0] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%。仅适用于年报。）
    EBIT_MARGIN = "EBIT_MARGIN"  # EBIT利润率 例如填写 [1.0,10.0] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    EBITDA_MARGIN = "EBITDA_MARGIN"  # EBITDA利润率 例如填写 [1.0,10.0] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    FINANCIAL_COST_RATE = "FINANCIAL_COST_RATE"  # 财务成本率 例如填写 [1.0,10.0] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    OPERATING_PROFIT_TTM = "OPERATING_PROFIT_TTM"  # 营业利润(TTM) 例如填写 [1000000000,1000000000] 值区间 （单位：元。仅适用于年报。）
    SHAREHOLDER_NET_PROFIT_TTM = (
        "SHAREHOLDER_NET_PROFIT_TTM"  # 归属于母公司的净利润 例如填写 [1000000000,1000000000] 值区间 （单位：元。仅适用于年报。）
    )
    NET_PROFIT_CASH_COVER_TTM = (
        "NET_PROFIT_CASH_COVER_TTM"  # 盈利中的现金收入比例 例如填写 [1.0,60.0] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%。仅适用于年报。）
    )
    CURRENT_RATIO = "CURRENT_RATIO"  # 偿债能力属性流动比率 例如填写 [100,250] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    QUICK_RATIO = "QUICK_RATIO"  # 速动比率 例如填写 [100,250] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    CURRENT_ASSET_RATIO = "CURRENT_ASSET_RATIO"  # 清债能力属性流动资产率 例如填写 [10,100] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    CURRENT_DEBT_RATIO = "CURRENT_DEBT_RATIO"  # 流动负债率 例如填写 [10,100] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    EQUITY_MULTIPLIER = "EQUITY_MULTIPLIER"  # 权益乘数 例如填写 [100,180] 值区间
    PROPERTY_RATIO = "PROPERTY_RATIO"  # 产权比率 例如填写 [50,100] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    CASH_AND_CASH_EQUIVALENTS = "CASH_AND_CASH_EQUIVALENTS"  # 现金和现金等价 例如填写 [1000000000,1000000000] 值区间（单位：元）
    TOTAL_ASSET_TURNOVER = "TOTAL_ASSET_TURNOVER"  # 运营能力属性总资产周转率 例如填写 [50,100] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    FIXED_ASSET_TURNOVER = "FIXED_ASSET_TURNOVER"  # 固定资产周转率 例如填写 [50,100] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    INVENTORY_TURNOVER = "INVENTORY_TURNOVER"  # 存货周转率 例如填写 [50,100] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    OPERATING_CASH_FLOW_TTM = "OPERATING_CASH_FLOW_TTM"  # 经营活动现金流(TTM) 例如填写 [1000000000,1000000000] 值区间（单位：元。仅适用于年报。）
    ACCOUNTS_RECEIVABLE = (
        "ACCOUNTS_RECEIVABLE"  # 应收帐款净额 例如填写 [1000000000,1000000000] 值区间 例如填写 [1000000000,1000000000] 值区间 （单位：元）
    )
    EBIT_GROWTH_RATE = "EBIT_GROWTH_RATE"  # 成长能力属性EBIT同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    OPERATING_PROFIT_GROWTH_RATE = (
        "OPERATING_PROFIT_GROWTH_RATE"  # 营业利润同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    )
    TOTAL_ASSETS_GROWTH_RATE = "TOTAL_ASSETS_GROWTH_RATE"  # 总资产同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    PROFIT_TO_SHAREHOLDERS_GROWTH_RATE = (
        "PROFIT_TO_SHAREHOLDERS_GROWTH_RATE"  # 归母净利润同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    )
    PROFIT_BEFORE_TAX_GROWTH_RATE = (
        "PROFIT_BEFORE_TAX_GROWTH_RATE"  # 总利润同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    )
    EPS_GROWTH_RATE = "EPS_GROWTH_RATE"  # EPS同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    ROE_GROWTH_RATE = "ROE_GROWTH_RATE"  # ROE同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    ROIC_GROWTH_RATE = "ROIC_GROWTH_RATE"  # ROIC同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    NOCF_GROWTH_RATE = "NOCF_GROWTH_RATE"  # 经营现金流同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    NOCF_PER_SHARE_GROWTH_RATE = (
        "NOCF_PER_SHARE_GROWTH_RATE"  # 每股经营现金流同比增长率 例如填写 [1.0,10.0] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    )
    OPERATING_REVENUE_CASH_COVER = (
        "OPERATING_REVENUE_CASH_COVER"  # 现金流属性经营现金收入比 例如填写 [10,100] 值区间（该字段为百分比字段，默认省略%，如20实际对应20%）
    )
    OPERATING_PROFIT_TO_TOTAL_PROFIT = (
        "OPERATING_PROFIT_TO_TOTAL_PROFIT"  # 营业利润占比 例如填写 [10,100] 值区间 （该字段为百分比字段，默认省略%，如20实际对应20%）
    )
    BASIC_EPS = "BASIC_EPS"  # 市场表现属性基本每股收益 例如填写 [0.1,10] 值区间 (单位：元)
    DILUTED_EPS = "DILUTED_EPS"  # 稀释每股收益 例如填写 [0.1,10] 值区间 (单位：元)
    NOCF_PER_SHARE = "NOCF_PER_SHARE"  # 每股经营现金净流量 例如填写 [0.1,10] 值区间 (单位：元)


class EPattern(Enum):
    NONE = ft.StockField.NONE
    MA_ALIGNMENT_LONG = ft.StockField.MA_ALIGNMENT_LONG  # MA多头排列（连续两天MA5>MA10>MA20>MA30>MA60，且当日收盘价大于前一天收盘价）
    MA_ALIGNMENT_SHORT = ft.StockField.MA_ALIGNMENT_SHORT  # MA空头排列（连续两天MA5 <MA10 <MA20 <MA30 <MA60，且当日收盘价小于前一天收盘价）
    EMA_ALIGNMENT_LONG = ft.StockField.EMA_ALIGNMENT_LONG  # EMA多头排列（连续两天EMA5>EMA10>EMA20>EMA30>EMA60，且当日收盘价大于前一天收盘价）
    EMA_ALIGNMENT_SHORT = (
        ft.StockField.EMA_ALIGNMENT_SHORT
    )  # EMA空头排列（连续两天EMA5 <EMA10 <EMA20 <EMA30 <EMA60，且当日收盘价小于前一天收盘价）
    RSI_GOLD_CROSS_LOW = ft.StockField.RSI_GOLD_CROSS_LOW  # RSI低位金叉（50以下，短线RSI上穿长线RSI（前一日短线RSI小于长线RSI，当日短线RSI大于长线RSI））
    RSI_DEATH_CROSS_HIGH = (
        ft.StockField.RSI_DEATH_CROSS_HIGH
    )  # RSI高位死叉（50以上，短线RSI下穿长线RSI（前一日短线RSI大于长线RSI，当日短线RSI小于长线RSI））
    RSI_TOP_DIVERGENCE = (
        ft.StockField.RSI_TOP_DIVERGENCE
    )  # RSI顶背离（相邻的两个K线波峰，后面的波峰对应的CLOSE>前面的波峰对应的CLOSE，后面波峰的RSI12值 <前面波峰的RSI12值）
    RSI_BOTTOM_DIVERGENCE = (
        ft.StockField.RSI_BOTTOM_DIVERGENCE
    )  # RSI底背离（相邻的两个K线波谷，后面的波谷对应的CLOSE <前面的波谷对应的CLOSE，后面波谷的RSI12值>前面波谷的RSI12值）
    KDJ_GOLD_CROSS_LOW = ft.StockField.KDJ_GOLD_CROSS_LOW  # KDJ低位金叉（KDJ的值都小于或等于30，且前一日K,J值分别小于D值，当日K,J值分别大于D值）
    KDJ_DEATH_CROSS_HIGH = ft.StockField.KDJ_DEATH_CROSS_HIGH  # KDJ高位死叉（KDJ的值都大于或等于70，且前一日K,J值分别大于D值，当日K,J值分别小于D值）
    KDJ_TOP_DIVERGENCE = (
        ft.StockField.KDJ_TOP_DIVERGENCE
    )  # KDJ顶背离（相邻的两个K线波峰，后面的波峰对应的CLOSE>前面的波峰对应的CLOSE，后面波峰的J值 <前面波峰的J值）
    KDJ_BOTTOM_DIVERGENCE = (
        ft.StockField.KDJ_BOTTOM_DIVERGENCE
    )  # KDJ底背离（相邻的两个K线波谷，后面的波谷对应的CLOSE <前面的波谷对应的CLOSE，后面波谷的J值>前面波谷的J值）
    MACD_GOLD_CROSS_LOW = ft.StockField.MACD_GOLD_CROSS_LOW  # MACD低位金叉（DIFF上穿DEA（前一日DIFF小于DEA，当日DIFF大于DEA））
    MACD_DEATH_CROSS_HIGH = ft.StockField.MACD_DEATH_CROSS_HIGH  # MACD高位死叉（DIFF下穿DEA（前一日DIFF大于DEA，当日DIFF小于DEA））
    MACD_TOP_DIVERGENCE = (
        ft.StockField.MACD_TOP_DIVERGENCE
    )  # MACD顶背离（相邻的两个K线波峰，后面的波峰对应的CLOSE>前面的波峰对应的CLOSE，后面波峰的macd值 <前面波峰的macd值）
    MACD_BOTTOM_DIVERGENCE = (
        ft.StockField.MACD_BOTTOM_DIVERGENCE
    )  # MACD底背离（相邻的两个K线波谷，后面的波谷对应的CLOSE <前面的波谷对应的CLOSE，后面波谷的macd值>前面波谷的macd值）
    BOLL_BREAK_UPPER = ft.StockField.BOLL_BREAK_UPPER  # BOLL突破上轨（前一日股价低于上轨值，当日股价大于上轨值）
    BOLL_BREAK_LOWER = ft.StockField.BOLL_BREAK_LOWER  # BOLL突破下轨（前一日股价高于下轨值，当日股价小于下轨值）
    BOLL_CROSS_MIDDLE_UP = ft.StockField.BOLL_CROSS_MIDDLE_UP  # BOLL向上破中轨（前一日股价低于中轨值，当日股价大于中轨值）
    BOLL_CROSS_MIDDLE_DOWN = ft.StockField.BOLL_CROSS_MIDDLE_DOWN  # BOLL向下破中轨（前一日股价大于中轨值，当日股价小于中轨值）


class EIndicator(Enum):
    NONE = ft.StockField.NONE
    PRICE = ft.StockField.PRICE  # 最新价格
    MA5 = ft.StockField.MA5  # 5日简单均线（不建议使用）
    MA10 = ft.StockField.MA10  # 10日简单均线（不建议使用）
    MA20 = ft.StockField.MA20  # 20日简单均线（不建议使用）
    MA30 = ft.StockField.MA30  # 30日简单均线（不建议使用）
    MA60 = ft.StockField.MA60  # 60日简单均线（不建议使用）
    MA120 = ft.StockField.MA120  # 120日简单均线（不建议使用）
    MA250 = ft.StockField.MA250  # 250日简单均线（不建议使用）
    RSI = ft.StockField.RSI  # RSI 指标参数的默认值为12
    EMA5 = ft.StockField.EMA5  # 5日指数移动均线（不建议使用）
    EMA10 = ft.StockField.EMA10  # 10日指数移动均线（不建议使用）
    EMA20 = ft.StockField.EMA20  # 20日指数移动均线（不建议使用）
    EMA30 = ft.StockField.EMA30  # 30日指数移动均线（不建议使用）
    EMA60 = ft.StockField.EMA60  # 60日指数移动均线（不建议使用）
    EMA120 = ft.StockField.EMA120  # 120日指数移动均线（不建议使用）
    EMA250 = ft.StockField.EMA250  # 250日指数移动均线（不建议使用）
    VALUE = ft.StockField.VALUE  # 自定义数值（stock_field1 不支持此字段）
    MA = ft.StockField.MA  # 简单均线
    EMA = ft.StockField.EMA  # 指数移动均线
    KDJ_K = ft.StockField.KDJ_K  # KDJ 指标的 K 值。指标参数需要根据 KDJ 进行传参。不传则默认为 [9,3,3]
    KDJ_D = ft.StockField.KDJ_D  # KDJ 指标的 D 值。指标参数需要根据 KDJ 进行传参。不传则默认为 [9,3,3]
    KDJ_J = ft.StockField.KDJ_J  # KDJ 指标的 J 值。指标参数需要根据 KDJ 进行传参。不传则默认为 [9,3,3]
    MACD_DIFF = ft.StockField.MACD_DIFF  # MACD 指标的 DIFF 值。指标参数需要根据 MACD 进行传参。不传则默认为 [12,26,9]
    MACD_DEA = ft.StockField.MACD_DEA  # MACD 指标的 DEA 值。指标参数需要根据 MACD 进行传参。不传则默认为 [12,26,9]
    MACD = ft.StockField.MACD  # MACD 指标的 MACD 值。指标参数需要根据 MACD 进行传参。不传则默认为 [12,26,9]
    BOLL_UPPER = ft.StockField.BOLL_UPPER  # BOLL 指标的 UPPER 值。指标参数需要根据 BOLL 进行传参。不传则默认为 [20,2]
    BOLL_MIDDLER = ft.StockField.BOLL_MIDDLER  # BOLL 指标的 MIDDLER 值。指标参数需要根据 BOLL 进行传参。不传则默认为 [20,2]
    BOLL_LOWER = ft.StockField.BOLL_LOWER  # BOLL 指标的 LOWER 值。指标参数需要根据 BOLL 进行传参。不传则默认为 [20,2]


class EFinancialQuarter(Enum):
    NONE = ft.FinancialQuarter.NONE
    ANNUAL = ft.FinancialQuarter.ANNUAL  # 年报
    FIRST_QUARTER = ft.FinancialQuarter.FIRST_QUARTER  # Q1一季报
    INTERIM = ft.FinancialQuarter.INTERIM  # Q6中期报
    THIRD_QUARTER = ft.FinancialQuarter.THIRD_QUARTER  # Q9三季报
    MOST_RECENT_QUARTER = ft.FinancialQuarter.MOST_RECENT_QUARTER  # 最近季报


class ERelativePosition(Enum):
    NONE = ft.RelativePosition.NONE  # 未知
    MORE = ft.RelativePosition.MORE  # 大于，first位于second的上方
    LESS = ft.RelativePosition.LESS  # 小于，first位于second的下方
    CROSS_UP = ft.RelativePosition.CROSS_UP  # 升穿，first从下往上穿second
    CROSS_DOWN = ft.RelativePosition.CROSS_DOWN  # 跌穿，first从上往下穿second


class EKLType(Enum):
    NONE = ft.KLType.NONE
    K_1M = ft.KLType.K_1M
    K_3M = ft.KLType.K_3M
    K_5M = ft.KLType.K_5M
    K_15M = ft.KLType.K_15M
    K_30M = ft.KLType.K_30M
    K_60M = ft.KLType.K_60M
    K_DAY = ft.KLType.K_DAY
    K_WEEK = ft.KLType.K_WEEK
    K_MON = ft.KLType.K_MON
    K_QUARTER = ft.KLType.K_QUARTER
    K_YEAR = ft.KLType.K_YEAR


def convert_to_stock_field(field: EPattern | EIndicator | EFinancial) -> ft.StockField:
    result = getattr(ft.StockField, field.name)

    return result


def convert_to_fiancial_quater(field: EFinancialQuarter) -> ft.FinancialQuarter:
    result = getattr(ft.FinancialQuarter, field.name)

    return result


def convert_to_relative_position(field: ERelativePosition) -> ft.RelativePosition:
    result = getattr(ft.RelativePosition, field.name)

    return result


def convert_to_market(field: EMarket) -> ft.Market:
    result = getattr(ft.Market, field.name)

    return result


def convert_to_kltype(kltype: EKLType) -> ft.KLType:
    result = getattr(ft.KLType, kltype.name)

    return result


def extract_vt_symbol(vt_symbol: str) -> Tuple[str, Exchange]:
    """
    :return: (symbol, exchange)
    """
    symbol, exchange_str = vt_symbol.split(".")
    return symbol, Exchange(exchange_str)


def generate_vt_symbol(symbol: str, exchange: Exchange) -> str:
    """
    return vt_symbol
    """
    return f"{symbol}.{exchange.value}"


def convert_vt_symbol(vt_symbol) -> Tuple[str, Exchange]:
    """富途合约名称转换"""
    code_list = vt_symbol.split(".")
    futu_exchange = code_list[1]
    code = code_list[0]
    exchange = Exchange(futu_exchange)
    return code, exchange


def convert_symbol_futu2vt(code) -> Tuple[str, Exchange]:
    """富途合约名称转换"""
    code_list = code.split(".")
    futu_exchange = code_list[0]
    futu_symbol = ".".join(code_list[1:])
    exchange = EXCHANGE_FUTU2VT[futu_exchange]
    return futu_symbol, exchange


def convert_symbol_vt2futu(symbol, exchange) -> str:
    """veighna合约名称转换"""
    futu_exchange: Exchange = EXCHANGE_VT2FUTU[exchange]
    return f"{futu_exchange}.{symbol}"


def _convert_futucode_vt_symbol(code) -> str:
    code_list = code.split(".")

    code = code_list[1]
    futu_exchange = code_list[0]

    # assert futu_exchange == "HK", f"unsupported exchange {futu_exchange}"
    # exchange = Exchange.SEHK

    exchange = EXCHANGE_FUTU2VT[futu_exchange]

    vt_symbol = generate_vt_symbol(code, exchange)

    return vt_symbol


def _convert_vt_symbol_futucode(vt_symbol) -> str:
    code, exchange = extract_vt_symbol(vt_symbol)

    futu_exchange: str = EXCHANGE_VT2FUTU[exchange]

    ft_code = f"{futu_exchange}.{code}"

    return ft_code


def convert_ft_stock_list_to_vt_symbols(ft_stock_list: List[str]) -> List[str]:
    vt_stock_list = [_convert_futucode_vt_symbol(stock) for stock in ft_stock_list]

    return vt_stock_list


def convert_vt_symbols_to_futucodes(vt_stock_list: List[str]) -> List[str]:
    ft_stock_list = [_convert_vt_symbol_futucode(stock) for stock in vt_stock_list]

    return ft_stock_list


def get_selected_vt_stock_list(check_exclude: bool = False) -> List[str]:
    vnpy_trading_info = load_json("oxna_trading_info.json", use_comments=True)

    if check_exclude:
        vt_stock_list: List[str] = []
        for vt_symbol, symbol_info in vnpy_trading_info.items():
            exclude_symbol = True
            if exclude_symbol:
                if symbol_info.get("exclude", 0):
                    continue
            vt_stock_list.append(vt_symbol)
    else:
        vt_stock_list = list(vnpy_trading_info.keys())

    return vt_stock_list


def get_selected_ft_stock_list(check_exclude: bool = False) -> List[str]:
    vt_stock_list = get_selected_vt_stock_list(check_exclude)

    ft_stock_list = convert_vt_symbols_to_futucodes(vt_stock_list)

    return ft_stock_list


@lru_cache(maxsize=999)
def get_stock_basic_info(vt_symbol: str) -> dict:
    stock_basic_info = load_json("stock_basic_info.json")

    symbol_basic_info = stock_basic_info.get(vt_symbol, None)

    return symbol_basic_info


@lru_cache(maxsize=999)
def get_contracts_info() -> Dict[str, ContractData]:
    contracts_info = load_json("constracts_info.json")

    return contracts_info


def get_contract_info(vt_symbol: str) -> Optional[ContractData]:
    contracts_info = get_contracts_info()

    contract_info = contracts_info.get(vt_symbol, None)

    return contract_info


@lru_cache(maxsize=999)
def get_stock_trade_info(vt_symbol: str) -> dict:
    vnpy_trading_info_file = "vnpy_trading_info.json"
    vnpy_trading_info = load_json(vnpy_trading_info_file, use_comments=True)
    symbol_trade_info = vnpy_trading_info[vt_symbol]

    return symbol_trade_info


@lru_cache(maxsize=999)
def get_stock_price_tick(vt_symbol: str) -> float:
    symbol_basic_info: dict = get_stock_basic_info(vt_symbol)
    assert symbol_basic_info, f"{vt_symbol} doesn't exist in the stock basic info"

    price_tick: float = symbol_basic_info["price_tick"]

    return price_tick


@lru_cache(maxsize=999)
def get_stock_lot_size(vt_symbol: str) -> int:
    symbol_basic_info: dict = get_stock_basic_info(vt_symbol)
    assert symbol_basic_info, f"{vt_symbol} doesn't exist in the stock basic info"

    lot_size: int = symbol_basic_info["lot_size"]

    return lot_size


@lru_cache(maxsize=999)
def get_stock_display_name(vt_symbol: str) -> str:
    symbol_basic_info: dict = get_stock_basic_info(vt_symbol)
    assert symbol_basic_info, f"{vt_symbol} doesn't exist in the stock basic info"

    display_name: str = symbol_basic_info["display_name"]

    return display_name


def save_contracts_info_file(contracts: Dict[str, ContractData], output: Callable = None):
    output = output or print

    contracts_file: str = "constracts_info.json"
    output(colored(f"update contracts info {len(contracts)} to {contracts_file}...", "green"))

    simplified_contracts_info: Dict[str, dict] = {}

    fields: List[str] = [
        "symbol",
        "exchange",
        "name",
        "product",
        "size",
        "pricetick",
        "min_volume",
        "stop_supported",
    ]

    for vt_symbol, contract in contracts.items():
        simplified_contract_info = {}

        for f in fields:
            simplified_contract_info[f] = getattr(contract, f)

        simplified_contracts_info[vt_symbol] = simplified_contract_info

    save_json(contracts_file, simplified_contracts_info)


def save_basic_info_file(
    api, vt_stock_list: List[str], stock_info_file: str = "stock_basic_info.json", output: Callable = None
):
    output = output or print
    output(colored(f"update basic info {len(vt_stock_list)} to {stock_info_file}...", "green"))

    stock_info: dict = {}

    for vt_symbol in vt_stock_list:
        contract_data: ContractData = api.get_contract(vt_symbol)
        if contract_data:
            price_tick = contract_data.pricetick

            stock_info[vt_symbol] = {
                "price_tick": price_tick,
                "display_name": contract_data.name,
                "lot_size": contract_data.size,
            }

    if stock_info:
        save_json(stock_info_file, stock_info)


def load_connect_setting(connect_setting_path: str = "connect_futu.json", output: Callable = None) -> dict:
    output = output or print
    setting: dict = load_json(connect_setting_path)

    res = {}

    if not setting:
        output(colored(f"{connect_setting_path} not exists", "yellow"), logging.WARNING)

        res["host"] = "127.0.0.1"
        res["port"] = 11111
        res["market"] = "HK"
        res["trd_env"] = "simulate"
        res["password"] = "123456"
        res["contracts_cache_path"] = get_folder_path("contracts_cache")

        return res

    return setting
