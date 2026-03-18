#!/usr/bin/env python3
"""
金发科技（600143）技术分析脚本
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_ma(data, periods):
    """计算移动平均线"""
    for period in periods:
        data[f'MA{period}'] = data['Close'].rolling(window=period).mean()
    return data

def calculate_macd(data, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    data['MACD_DIF'] = ema_fast - ema_slow
    data['MACD_DEA'] = data['MACD_DIF'].ewm(span=signal, adjust=False).mean()
    data['MACD_HIST'] = 2 * (data['MACD_DIF'] - data['MACD_DEA'])
    return data

def calculate_bollinger(data, period=20, std_dev=2):
    """计算布林带"""
    data['BOLL_MID'] = data['Close'].rolling(window=period).mean()
    data['BOLL_STD'] = data['Close'].rolling(window=period).std()
    data['BOLL_UP'] = data['BOLL_MID'] + (data['BOLL_STD'] * std_dev)
    data['BOLL_DOWN'] = data['BOLL_MID'] - (data['BOLL_STD'] * std_dev)
    data['BOLL_WIDTH'] = (data['BOLL_UP'] - data['BOLL_DOWN']) / data['BOLL_MID']
    return data

def calculate_kdj(data, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    low_list = data['Low'].rolling(window=n, min_periods=n).min()
    high_list = data['High'].rolling(window=n, min_periods=n).max()
    rsv = (data['Close'] - low_list) / (high_list - low_list) * 100
    
    data['KDJ_K'] = rsv.ewm(com=m1-1, adjust=False).mean()
    data['KDJ_D'] = data['KDJ_K'].ewm(com=m2-1, adjust=False).mean()
    data['KDJ_J'] = 3 * data['KDJ_K'] - 2 * data['KDJ_D']
    return data

def analyze_ma(data):
    """分析均线系统"""
    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else latest
    
    ma5, ma10, ma20, ma60 = latest['MA5'], latest['MA10'], latest['MA20'], latest['MA60']
    
    # 判断多头排列
    bullish_arrangement = ma5 > ma10 > ma20 > ma60
    bearish_arrangement = ma5 < ma10 < ma20 < ma60
    
    # 金叉死叉判断
    ma5_cross_ma10 = (prev['MA5'] <= prev['MA10'] and ma5 > ma10)
    ma5_dead_cross_ma10 = (prev['MA5'] >= prev['MA10'] and ma5 < ma10)
    
    return {
        'MA5': ma5, 'MA10': ma10, 'MA20': ma20, 'MA60': ma60,
        '多头排列': bullish_arrangement,
        '空头排列': bearish_arrangement,
        'MA5上穿MA10': ma5_cross_ma10,
        'MA5下穿MA10': ma5_dead_cross_ma10,
        '最新价': latest['Close']
    }

def analyze_macd(data):
    """分析MACD"""
    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else latest
    
    dif, dea, hist = latest['MACD_DIF'], latest['MACD_DEA'], latest['MACD_HIST']
    
    # 金叉死叉
    golden_cross = (prev['MACD_DIF'] <= prev['MACD_DEA'] and dif > dea)
    dead_cross = (prev['MACD_DIF'] >= prev['MACD_DEA'] and dif < dea)
    
    # 柱状图趋势
    hist_trend = "扩大" if hist > prev['MACD_HIST'] else "缩小"
    
    return {
        'DIF': dif, 'DEA': dea, '柱状图': hist,
        '金叉': golden_cross, '死叉': dead_cross,
        '柱状图趋势': hist_trend,
        '零轴上方': dif > 0 and dea > 0
    }

def analyze_bollinger(data):
    """分析布林带"""
    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else latest
    
    close = latest['Close']
    mid, up, down = latest['BOLL_MID'], latest['BOLL_UP'], latest['BOLL_DOWN']
    width = latest['BOLL_WIDTH']
    prev_width = prev['BOLL_WIDTH'] if len(data) > 1 else width
    
    # 位置判断
    if close > up:
        position = "上轨上方（超买）"
    elif close > mid:
        position = "中轨与上轨之间（强势）"
    elif close > down:
        position = "中轨与下轨之间（弱势）"
    else:
        position = "下轨下方（超卖）"
    
    # 收口/开口
    if width > prev_width * 1.05:
        band_status = "开口（波动扩大）"
    elif width < prev_width * 0.95:
        band_status = "收口（波动缩小）"
    else:
        band_status = "走平"
    
    return {
        '上轨': up, '中轨': mid, '下轨': down,
        '位置': position,
        '带宽状态': band_status,
        '带宽': width
    }

def analyze_kdj(data):
    """分析KDJ"""
    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else latest
    
    k, d, j = latest['KDJ_K'], latest['KDJ_D'], latest['KDJ_J']
    
    # 金叉死叉
    golden_cross = (prev['KDJ_K'] <= prev['KDJ_D'] and k > d)
    dead_cross = (prev['KDJ_K'] >= prev['KDJ_D'] and k < d)
    
    # 超买超卖
    if j > 100:
        status = "严重超买"
    elif j > 80:
        status = "超买区"
    elif j < 0:
        status = "严重超卖"
    elif j < 20:
        status = "超卖区"
    else:
        status = "中性区"
    
    return {
        'K值': k, 'D值': d, 'J值': j,
        '金叉': golden_cross, '死叉': dead_cross,
        '状态': status
    }

def detect_waves(data):
    """
    简易波浪理论识别
    基于价格高低点识别可能的波浪结构
    """
    # 获取近期数据点
    closes = data['Close'].values
    highs = data['High'].values
    lows = data['Low'].values
    
    if len(closes) < 20:
        return "数据不足"
    
    # 寻找局部极值点（简化版）
    recent_high = np.max(highs[-20:])
    recent_low = np.min(lows[-20:])
    current = closes[-1]
    
    # 简单判断趋势
    trend_5 = closes[-1] - closes[-6] if len(closes) >= 6 else 0
    trend_20 = closes[-1] - closes[-21] if len(closes) >= 21 else 0
    
    # 基于趋势和位置推测波浪
    if trend_20 > 0:  # 大趋势向上
        if current > np.mean(closes[-10:]):
            if trend_5 > 0:
                return "可能处于第3浪或第5浪上升阶段"
            else:
                return "可能处于第4浪调整或第5浪尾声"
        else:
            return "可能处于第2浪或第4浪调整"
    else:  # 大趋势向下或盘整
        if trend_5 > 0:
            return "可能处于B浪反弹"
        else:
            return "可能处于A浪下跌或C浪下跌"

def get_period_analysis(ticker, period, interval):
    """获取指定周期的分析"""
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    if data.empty or len(data) < 30:
        return None, "数据不足"
    
    # 重命名列（yfinance返回MultiIndex列）
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # 计算指标
    data = calculate_ma(data, [5, 10, 20, 60])
    data = calculate_macd(data)
    data = calculate_bollinger(data)
    data = calculate_kdj(data)
    
    # 分析
    ma_analysis = analyze_ma(data)
    macd_analysis = analyze_macd(data)
    boll_analysis = analyze_bollinger(data)
    kdj_analysis = analyze_kdj(data)
    wave_analysis = detect_waves(data)
    
    return {
        '均线': ma_analysis,
        'MACD': macd_analysis,
        '布林带': boll_analysis,
        'KDJ': kdj_analysis,
        '波浪': wave_analysis,
        '最新价': data['Close'].iloc[-1],
        '数据条数': len(data)
    }, data

def main():
    ticker = "600143.SS"  # 金发科技 - 上海A股
    
    print("=" * 60)
    print("金发科技（600143）技术分析报告")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 日线分析
    print("\n" + "=" * 60)
    print("【日线分析】- 近1年数据")
    print("=" * 60)
    daily_result, daily_data = get_period_analysis(ticker, "1y", "1d")
    
    if daily_result:
        print(f"\n当前价格：{daily_result['最新价']:.2f}")
        print(f"\n1. 波浪理论：{daily_result['波浪']}")
        
        print(f"\n2. 均线系统：")
        ma = daily_result['均线']
        print(f"   MA5: {ma['MA5']:.2f} | MA10: {ma['MA10']:.2f} | MA20: {ma['MA20']:.2f} | MA60: {ma['MA60']:.2f}")
        print(f"   多头排列：{'是' if ma['多头排列'] else '否'} | 空头排列：{'是' if ma['空头排列'] else '否'}")
        if ma['MA5上穿MA10']:
            print(f"   ⚠️ MA5上穿MA10（金叉信号）")
        if ma['MA5下穿MA10']:
            print(f"   ⚠️ MA5下穿MA10（死叉信号）")
        
        print(f"\n3. MACD指标：")
        macd = daily_result['MACD']
        print(f"   DIF: {macd['DIF']:.3f} | DEA: {macd['DEA']:.3f} | 柱状图: {macd['柱状图']:.3f}")
        print(f"   位置：{'零轴上方' if macd['零轴上方'] else '零轴下方'}")
        print(f"   柱状图趋势：{macd['柱状图趋势']}")
        if macd['金叉']:
            print(f"   ⚠️ MACD金叉信号")
        if macd['死叉']:
            print(f"   ⚠️ MACD死叉信号")
        
        print(f"\n4. 布林带：")
        boll = daily_result['布林带']
        print(f"   上轨: {boll['上轨']:.2f} | 中轨: {boll['中轨']:.2f} | 下轨: {boll['下轨']:.2f}")
        print(f"   价格位置：{boll['位置']}")
        print(f"   带宽状态：{boll['带宽状态']}")
        
        print(f"\n5. KDJ指标：")
        kdj = daily_result['KDJ']
        print(f"   K: {kdj['K值']:.2f} | D: {kdj['D值']:.2f} | J: {kdj['J值']:.2f}")
        print(f"   状态：{kdj['状态']}")
        if kdj['金叉']:
            print(f"   ⚠️ KDJ金叉信号")
        if kdj['死叉']:
            print(f"   ⚠️ KDJ死叉信号")
    
    # 周线分析
    print("\n" + "=" * 60)
    print("【周线分析】- 近3年数据")
    print("=" * 60)
    weekly_result, weekly_data = get_period_analysis(ticker, "3y", "1wk")
    
    if weekly_result:
        print(f"\n当前价格：{weekly_result['最新价']:.2f}")
        print(f"\n1. 波浪理论：{weekly_result['波浪']}")
        
        print(f"\n2. 均线系统：")
        ma = weekly_result['均线']
        print(f"   MA5: {ma['MA5']:.2f} | MA10: {ma['MA10']:.2f} | MA20: {ma['MA20']:.2f} | MA60: {ma['MA60']:.2f}")
        print(f"   多头排列：{'是' if ma['多头排列'] else '否'} | 空头排列：{'是' if ma['空头排列'] else '否'}")
        
        print(f"\n3. MACD指标：")
        macd = weekly_result['MACD']
        print(f"   DIF: {macd['DIF']:.3f} | DEA: {macd['DEA']:.3f} | 柱状图: {macd['柱状图']:.3f}")
        print(f"   位置：{'零轴上方' if macd['零轴上方'] else '零轴下方'}")
        if macd['金叉']:
            print(f"   ⚠️ MACD金叉信号")
        if macd['死叉']:
            print(f"   ⚠️ MACD死叉信号")
        
        print(f"\n4. 布林带：")
        boll = weekly_result['布林带']
        print(f"   上轨: {boll['上轨']:.2f} | 中轨: {boll['中轨']:.2f} | 下轨: {boll['下轨']:.2f}")
        print(f"   价格位置：{boll['位置']}")
        
        print(f"\n5. KDJ指标：")
        kdj = weekly_result['KDJ']
        print(f"   K: {kdj['K值']:.2f} | D: {kdj['D值']:.2f} | J: {kdj['J值']:.2f}")
        print(f"   状态：{kdj['状态']}")
    
    # 月线分析
    print("\n" + "=" * 60)
    print("【月线分析】- 近5年数据")
    print("=" * 60)
    monthly_result, monthly_data = get_period_analysis(ticker, "5y", "1mo")
    
    if monthly_result:
        print(f"\n当前价格：{monthly_result['最新价']:.2f}")
        print(f"\n1. 波浪理论：{monthly_result['波浪']}")
        
        print(f"\n2. 均线系统：")
        ma = monthly_result['均线']
        print(f"   MA5: {ma['MA5']:.2f} | MA10: {ma['MA10']:.2f} | MA20: {ma['MA20']:.2f} | MA60: {ma['MA60']:.2f}")
        print(f"   多头排列：{'是' if ma['多头排列'] else '否'} | 空头排列：{'是' if ma['空头排列'] else '否'}")
        
        print(f"\n3. MACD指标：")
        macd = monthly_result['MACD']
        print(f"   DIF: {macd['DIF']:.3f} | DEA: {macd['DEA']:.3f} | 柱状图: {macd['柱状图']:.3f}")
        print(f"   位置：{'零轴上方' if macd['零轴上方'] else '零轴下方'}")
        
        print(f"\n4. 布林带：")
        boll = monthly_result['布林带']
        print(f"   上轨: {boll['上轨']:.2f} | 中轨: {boll['中轨']:.2f} | 下轨: {boll['下轨']:.2f}")
        print(f"   价格位置：{boll['位置']}")
        
        print(f"\n5. KDJ指标：")
        kdj = monthly_result['KDJ']
        print(f"   K: {kdj['K值']:.2f} | D: {kdj['D值']:.2f} | J: {kdj['J值']:.2f}")
        print(f"   状态：{kdj['状态']}")
    
    # 综合判断
    print("\n" + "=" * 60)
    print("【综合判断】")
    print("=" * 60)
    
    if daily_result and weekly_result and monthly_result:
        # 支撑位和阻力位计算
        daily_boll = daily_result['布林带']
        weekly_boll = weekly_result['布林带']
        
        support_levels = []
        resistance_levels = []
        
        # 从布林带获取支撑阻力
        support_levels.append(daily_boll['下轨'])
        support_levels.append(daily_boll['中轨'])
        support_levels.append(weekly_boll['下轨'])
        
        resistance_levels.append(daily_boll['上轨'])
        resistance_levels.append(weekly_boll['上轨'])
        resistance_levels.append(weekly_boll['中轨'])
        
        support_levels = sorted([s for s in support_levels if s < daily_result['最新价']], reverse=True)[:3]
        resistance_levels = sorted([r for r in resistance_levels if r > daily_result['最新价']])[:3]
        
        print(f"\n📊 各周期技术面总结：")
        print(f"\n   日线级别：")
        d_bull = daily_result['均线']['多头排列']
        d_bear = daily_result['均线']['空头排列']
        d_macd_up = daily_result['MACD']['零轴上方']
        print(f"   - 趋势：{'多头排列' if d_bull else ('空头排列' if d_bear else '震荡整理')}")
        print(f"   - MACD：{'强势区' if d_macd_up else '弱势区'}")
        print(f"   - KDJ：{daily_result['KDJ']['状态']}")
        
        print(f"\n   周线级别：")
        w_bull = weekly_result['均线']['多头排列']
        w_bear = weekly_result['均线']['空头排列']
        w_macd_up = weekly_result['MACD']['零轴上方']
        print(f"   - 趋势：{'多头排列' if w_bull else ('空头排列' if w_bear else '震荡整理')}")
        print(f"   - MACD：{'强势区' if w_macd_up else '弱势区'}")
        
        print(f"\n   月线级别：")
        m_bull = monthly_result['均线']['多头排列']
        m_bear = monthly_result['均线']['空头排列']
        m_macd_up = monthly_result['MACD']['零轴上方']
        print(f"   - 趋势：{'多头排列' if m_bull else ('空头排列' if m_bear else '震荡整理')}")
        print(f"   - MACD：{'强势区' if m_macd_up else '弱势区'}")
        
        print(f"\n🎯 关键支撑位：")
        for i, s in enumerate(support_levels, 1):
            print(f"   支撑{i}: {s:.2f}")
        
        print(f"\n🎯 关键阻力位：")
        for i, r in enumerate(resistance_levels, 1):
            print(f"   阻力{i}: {r:.2f}")
        
        # 操作建议
        print(f"\n📋 操作建议：")
        
        # 多周期综合判断逻辑
        bullish_signals = sum([
            d_bull, w_bull, m_bull,
            d_macd_up, w_macd_up, m_macd_up,
            daily_result['KDJ']['状态'] not in ['超买区', '严重超买']
        ])
        
        bearish_signals = sum([
            d_bear, w_bear, m_bear,
            not d_macd_up, not w_macd_up, not m_macd_up,
            daily_result['KDJ']['状态'] in ['超买区', '严重超买']
        ])
        
        if bullish_signals >= 4:
            suggestion = "买入/持有"
            reason = "多周期指标共振向好，中长期趋势有望延续"
        elif bearish_signals >= 4:
            suggestion = "卖出/观望"
            reason = "多周期指标走弱，建议规避短期风险"
        else:
            suggestion = "观望"
            reason = "各周期信号不一致，建议等待趋势明朗"
        
        print(f"   建议：{suggestion}")
        print(f"   理由：{reason}")
        
        print(f"\n⚠️ 风险提示：")
        print(f"   1. 本分析仅供参考，不构成投资建议")
        print(f"   2. 股市有风险，投资需谨慎")
        print(f"   3. 波浪理论为主观判断，实际走势可能偏离")
        print(f"   4. 建议结合基本面分析和市场环境综合决策")
        print(f"   5. 注意市场整体风险及个股特殊风险")

if __name__ == "__main__":
    main()
