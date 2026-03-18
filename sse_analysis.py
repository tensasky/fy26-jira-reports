#!/usr/bin/env python3
"""上证指数技术面分析脚本"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import talib
import warnings
warnings.filterwarnings('ignore')

def get_stock_data(symbol, period="6mo"):
    """获取股票数据"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period)
    return df

def calculate_ma(df):
    """计算移动平均线"""
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df

def calculate_macd(df):
    """计算MACD指标"""
    df['DIF'], df['DEA'], df['MACD_Hist'] = talib.MACD(
        df['Close'], fastperiod=12, slowperiod=26, signalperiod=9
    )
    return df

def calculate_boll(df):
    """计算布林带"""
    df['BOLL_MID'] = df['Close'].rolling(window=20).mean()
    df['BOLL_STD'] = df['Close'].rolling(window=20).std()
    df['BOLL_UP'] = df['BOLL_MID'] + 2 * df['BOLL_STD']
    df['BOLL_DOWN'] = df['BOLL_MID'] - 2 * df['BOLL_STD']
    return df

def calculate_kdj(df):
    """计算KDJ指标"""
    low_list = df['Low'].rolling(window=9).min()
    high_list = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_list) / (high_list - low_list) * 100
    
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df

def analyze_wave_theory(df):
    """波浪理论分析 - 基于趋势和形态"""
    recent_highs = []
    recent_lows = []
    
    # 获取最近30个交易日的数据
    recent_df = df.tail(30)
    
    # 识别近期高低点
    for i in range(2, len(recent_df)-2):
        if recent_df['Close'].iloc[i] > recent_df['Close'].iloc[i-1] and \
           recent_df['Close'].iloc[i] > recent_df['Close'].iloc[i+1]:
            recent_highs.append((recent_df.index[i], recent_df['Close'].iloc[i]))
        if recent_df['Close'].iloc[i] < recent_df['Close'].iloc[i-1] and \
           recent_df['Close'].iloc[i] < recent_df['Close'].iloc[i+1]:
            recent_lows.append((recent_df.index[i], recent_df['Close'].iloc[i]))
    
    return recent_highs, recent_lows

def analyze_ma_system(df):
    """分析均线系统"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    mas = {
        'MA5': latest['MA5'],
        'MA10': latest['MA10'],
        'MA20': latest['MA20'],
        'MA60': latest['MA60']
    }
    
    # 判断多头排列
    bullish_arrangement = latest['MA5'] > latest['MA10'] > latest['MA20'] > latest['MA60']
    bearish_arrangement = latest['MA5'] < latest['MA10'] < latest['MA20'] < latest['MA60']
    
    # 金叉死叉判断
    ma5_cross_up = prev['MA5'] <= prev['MA10'] and latest['MA5'] > latest['MA10']
    ma5_cross_down = prev['MA5'] >= prev['MA10'] and latest['MA5'] < latest['MA10']
    
    return mas, bullish_arrangement, bearish_arrangement, ma5_cross_up, ma5_cross_down

def analyze_macd(df):
    """分析MACD"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    golden_cross = prev['DIF'] <= prev['DEA'] and latest['DIF'] > latest['DEA']
    death_cross = prev['DIF'] >= prev['DEA'] and latest['DIF'] < latest['DEA']
    
    # 背离检查
    price_trend = df['Close'].iloc[-10:].mean() - df['Close'].iloc[-20:-10].mean()
    macd_trend = df['MACD_Hist'].iloc[-10:].mean() - df['MACD_Hist'].iloc[-20:-10].mean()
    
    divergence = (price_trend > 0 and macd_trend < 0) or (price_trend < 0 and macd_trend > 0)
    
    return latest['DIF'], latest['DEA'], latest['MACD_Hist'], golden_cross, death_cross, divergence

def analyze_boll(df):
    """分析布林带"""
    latest = df.iloc[-1]
    
    # 计算带宽（收口/开口）
    bandwidth = (latest['BOLL_UP'] - latest['BOLL_DOWN']) / latest['BOLL_MID'] * 100
    prev_bandwidth = ((df.iloc[-5]['BOLL_UP'] - df.iloc[-5]['BOLL_DOWN']) / df.iloc[-5]['BOLL_MID'] * 100)
    
    narrowing = bandwidth < prev_bandwidth * 0.95  # 收口
    expanding = bandwidth > prev_bandwidth * 1.05  # 开口
    
    # 价格位置
    price_position = "中轨附近"
    if latest['Close'] > latest['BOLL_UP']:
        price_position = "上轨上方（超买区）"
    elif latest['Close'] < latest['BOLL_DOWN']:
        price_position = "下轨下方（超卖区）"
    elif latest['Close'] > latest['BOLL_MID']:
        price_position = "中轨上方"
    else:
        price_position = "中轨下方"
    
    return latest['BOLL_UP'], latest['BOLL_MID'], latest['BOLL_DOWN'], bandwidth, narrowing, expanding, price_position

def analyze_kdj(df):
    """分析KDJ"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    golden_cross = prev['K'] <= prev['D'] and latest['K'] > latest['D']
    death_cross = prev['K'] >= prev['D'] and latest['K'] < latest['D']
    
    # 超买超卖
    overbought = latest['J'] > 80
    oversold = latest['J'] < 20
    
    return latest['K'], latest['D'], latest['J'], golden_cross, death_cross, overbought, oversold

def find_support_resistance(df, n=20):
    """寻找支撑位和阻力位"""
    recent_df = df.tail(n)
    
    # 近期最高点作为阻力位
    resistance = recent_df['High'].max()
    # 近期最低点作为支撑位
    support = recent_df['Low'].min()
    
    # 更强的支撑/阻力（更多触及次数）
    all_highs = df['High'].tail(60)
    all_lows = df['Low'].tail(60)
    
    # 次强支撑/阻力
    support_2 = df['MA20'].iloc[-1]
    support_3 = df['MA60'].iloc[-1]
    
    return resistance, support, support_2, support_3

def main():
    print("=" * 60)
    print("上证指数（000001.SS）技术面分析报告")
    print("分析时间:", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)
    
    # 获取数据
    print("\n📊 正在获取数据...")
    df = get_stock_data("000001.SS", period="6mo")
    
    if df.empty:
        print("❌ 无法获取数据，请检查网络连接")
        return
    
    # 计算指标
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_boll(df)
    df = calculate_kdj(df)
    
    latest = df.iloc[-1]
    current_price = latest['Close']
    
    print(f"\n💰 当前价格: {current_price:.2f}")
    print(f"📈 今日涨跌: {latest['Close'] - df.iloc[-2]['Close']:.2f}")
    print(f"📊 成交量: {latest['Volume']/10000:.0f}万手")
    
    # 1. 波浪理论分析
    print("\n" + "=" * 60)
    print("1️⃣ 波浪理论分析")
    print("=" * 60)
    
    highs, lows = analyze_wave_theory(df)
    
    # 判断趋势
    price_change_20 = (df['Close'].iloc[-1] - df['Close'].iloc[-20]) / df['Close'].iloc[-20] * 100
    price_change_60 = (df['Close'].iloc[-1] - df['Close'].iloc[-60]) / df['Close'].iloc[-60] * 100
    
    print(f"   近20日涨跌幅: {price_change_20:.2f}%")
    print(f"   近60日涨跌幅: {price_change_60:.2f}%")
    
    if price_change_60 > 10 and price_change_20 > 0:
        print("   🌊 波浪判断: 可能处于第3浪或第5浪上升阶段")
        print("   💡 特征: 中长期趋势向上，短期动能较强")
    elif price_change_60 > 10 and price_change_20 < -5:
        print("   🌊 波浪判断: 可能处于第4浪调整或B浪反弹")
        print("   💡 特征: 中长期向上但短期回调")
    elif price_change_60 < 0 and price_change_20 < -5:
        print("   🌊 波浪判断: 可能处于A浪下跌或C浪主跌")
        print("   💡 特征: 趋势向下，空头主导")
    elif price_change_60 < 0 and price_change_20 > 3:
        print("   🌊 波浪判断: 可能处于B浪反弹或第2浪调整结束")
        print("   💡 特征: 下跌趋势中的反弹")
    else:
        print("   🌊 波浪判断: 处于震荡整理阶段")
        print("   💡 特征: 方向不明，等待突破")
    
    # 2. 均线系统分析
    print("\n" + "=" * 60)
    print("2️⃣ 均线系统分析 (MA5/10/20/60)")
    print("=" * 60)
    
    mas, bullish_arr, bearish_arr, ma5_golden, ma5_death = analyze_ma_system(df)
    
    print(f"   MA5:  {mas['MA5']:.2f}")
    print(f"   MA10: {mas['MA10']:.2f}")
    print(f"   MA20: {mas['MA20']:.2f}")
    print(f"   MA60: {mas['MA60']:.2f}")
    
    if bullish_arr:
        print("   ✅ 多头排列: MA5 > MA10 > MA20 > MA60，趋势向上")
    elif bearish_arr:
        print("   ⚠️ 空头排列: MA5 < MA10 < MA20 < MA60，趋势向下")
    else:
        print("   ⚖️ 均线交织: 方向待确认")
    
    if ma5_golden:
        print("   🔔 MA5上穿MA10形成金叉，短期看涨信号")
    elif ma5_death:
        print("   🔔 MA5下穿MA10形成死叉，短期看跌信号")
    
    # 3. MACD分析
    print("\n" + "=" * 60)
    print("3️⃣ MACD分析")
    print("=" * 60)
    
    dif, dea, hist, macd_golden, macd_death, divergence = analyze_macd(df)
    
    print(f"   DIF: {dif:.4f}")
    print(f"   DEA: {dea:.4f}")
    print(f"   MACD柱状图: {hist:.4f}")
    
    if hist > 0:
        print("   📊 柱状图在零轴上方，多头市场")
    else:
        print("   📊 柱状图在零轴下方，空头市场")
    
    if macd_golden:
        print("   🔔 DIF上穿DEA形成金叉，买入信号")
    elif macd_death:
        print("   🔔 DIF下穿DEA形成死叉，卖出信号")
    
    if divergence:
        print("   ⚠️ 发现价格与MACD背离，警惕趋势反转")
    
    # 4. 布林带分析
    print("\n" + "=" * 60)
    print("4️⃣ 布林带分析 (BOLL)")
    print("=" * 60)
    
    boll_up, boll_mid, boll_down, bandwidth, narrowing, expanding, position = analyze_boll(df)
    
    print(f"   上轨: {boll_up:.2f}")
    print(f"   中轨: {boll_mid:.2f}")
    print(f"   下轨: {boll_down:.2f}")
    print(f"   带宽: {bandwidth:.2f}%")
    
    print(f"   价格位置: {position}")
    
    if narrowing:
        print("   ⚡ 布林带收口，预示即将变盘")
    elif expanding:
        print("   📈 布林带开口，趋势加速中")
    
    # 5. KDJ分析
    print("\n" + "=" * 60)
    print("5️⃣ KDJ分析")
    print("=" * 60)
    
    k, d, j, kdj_golden, kdj_death, overbought, oversold = analyze_kdj(df)
    
    print(f"   K值: {k:.2f}")
    print(f"   D值: {d:.2f}")
    print(f"   J值: {j:.2f}")
    
    if overbought:
        print("   ⚠️ J值大于80，超买区域，警惕回调")
    elif oversold:
        print("   ✅ J值小于20，超卖区域，关注反弹")
    else:
        print("   ⚖️ KDJ处于正常区间")
    
    if kdj_golden:
        print("   🔔 K上穿D形成金叉，买入信号")
    elif kdj_death:
        print("   🔔 K下穿D形成死叉，卖出信号")
    
    # 支撑阻力位
    print("\n" + "=" * 60)
    print("📍 关键支撑位与阻力位")
    print("=" * 60)
    
    res, sup, sup2, sup3 = find_support_resistance(df)
    
    print(f"   🔴 第一阻力位: {res:.2f} (近期高点)")
    print(f"   🟡 第二阻力位: {boll_up:.2f} (布林上轨)")
    print(f"")
    print(f"   🟢 第一支撑位: {sup:.2f} (近期低点)")
    print(f"   🟢 第二支撑位: {sup2:.2f} (MA20)")
    print(f"   🟢 第三支撑位: {sup3:.2f} (MA60)")
    print(f"   🟢 第四支撑位: {boll_down:.2f} (布林下轨)")
    
    # 技术面总结
    print("\n" + "=" * 60)
    print("📝 技术面总结")
    print("=" * 60)
    
    bullish_signals = 0
    bearish_signals = 0
    
    if bullish_arr: bullish_signals += 1
    if ma5_golden: bullish_signals += 1
    if macd_golden: bullish_signals += 1
    if hist > 0: bullish_signals += 1
    if kdj_golden: bullish_signals += 1
    if position == "中轨上方": bullish_signals += 1
    
    if bearish_arr: bearish_signals += 1
    if ma5_death: bearish_signals += 1
    if macd_death: bearish_signals += 1
    if hist < 0: bearish_signals += 1
    if kdj_death: bearish_signals += 1
    if position == "中轨下方": bearish_signals += 1
    
    print(f"   看涨信号: {bullish_signals}个")
    print(f"   看跌信号: {bearish_signals}个")
    
    if bullish_signals > bearish_signals + 1:
        trend = "偏多"
    elif bearish_signals > bullish_signals + 1:
        trend = "偏空"
    else:
        trend = "震荡"
    
    print(f"   整体判断: {trend}")
    
    # 操作建议
    print("\n" + "=" * 60)
    print("💡 操作建议")
    print("=" * 60)
    
    if trend == "偏多":
        print("   操作建议: 持有或逢低买入")
        print("   入场区间: 回调至MA20/布林中轨附近")
        print("   止损位: 设置在MA60下方或近期低点")
    elif trend == "偏空":
        print("   操作建议: 减仓观望")
        print("   等待企稳信号: MACD金叉、KDJ超卖反弹")
        print("   不急于抄底，耐心等待趋势明朗")
    else:
        print("   操作建议: 轻仓观望")
        print("   当前处于震荡整理，方向不明")
        print("   等待突破关键支撑/阻力位后再操作")
    
    # 风险提示
    print("\n" + "=" * 60)
    print("⚠️ 风险提示")
    print("=" * 60)
    
    risks = []
    if divergence:
        risks.append("价格与MACD出现背离，需警惕反转风险")
    if overbought:
        risks.append("KDJ处于超买区，短期回调压力较大")
    if narrowing:
        risks.append("布林带收口，即将变盘，波动可能加大")
    if abs(price_change_20) > 10:
        risks.append("近期波动较大，注意控制风险敞口")
    
    if not risks:
        risks.append("市场运行相对平稳，但仍需关注突发消息影响")
    
    risks.append("技术指标具有滞后性，仅供参考")
    risks.append("股市有风险，投资需谨慎")
    
    for risk in risks:
        print(f"   • {risk}")
    
    print("\n" + "=" * 60)
    print("报告生成完毕")
    print("=" * 60)

if __name__ == "__main__":
    main()
