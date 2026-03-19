#!/usr/bin/env python3
"""
金发科技（600143）技术分析脚本 - 优化版
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_indicators(data):
    """计算所有技术指标"""
    # 重命名列（yfinance返回MultiIndex列）
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # 移动平均线
    for period in [5, 10, 20, 60]:
        data[f'MA{period}'] = data['Close'].rolling(window=period).mean()
    
    # MACD
    ema_fast = data['Close'].ewm(span=12, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=26, adjust=False).mean()
    data['DIF'] = ema_fast - ema_slow
    data['DEA'] = data['DIF'].ewm(span=9, adjust=False).mean()
    data['MACD_HIST'] = 2 * (data['DIF'] - data['DEA'])
    
    # 布林带
    data['BOLL_MID'] = data['Close'].rolling(window=20).mean()
    boll_std = data['Close'].rolling(window=20).std()
    data['BOLL_UP'] = data['BOLL_MID'] + (boll_std * 2)
    data['BOLL_DOWN'] = data['BOLL_MID'] - (boll_std * 2)
    
    # KDJ
    low_list = data['Low'].rolling(window=9, min_periods=9).min()
    high_list = data['High'].rolling(window=9, min_periods=9).max()
    rsv = (data['Close'] - low_list) / (high_list - low_list) * 100
    data['K'] = rsv.ewm(com=2, adjust=False).mean()
    data['D'] = data['K'].ewm(com=2, adjust=False).mean()
    data['J'] = 3 * data['K'] - 2 * data['D']
    
    return data

def analyze_period(data, period_name):
    """分析单个周期"""
    if data is None or len(data) < 30:
        return None
    
    data = calculate_indicators(data)
    latest = data.iloc[-1]
    prev = data.iloc[-2]
    
    result = {
        'period': period_name,
        'close': latest['Close'],
        'ma': {
            'MA5': latest['MA5'], 'MA10': latest['MA10'], 
            'MA20': latest['MA20'], 'MA60': latest['MA60'],
            'bullish': latest['MA5'] > latest['MA10'] > latest['MA20'] > latest['MA60'],
            'bearish': latest['MA5'] < latest['MA10'] < latest['MA20'] < latest['MA60'],
            'ma5_cross_up': prev['MA5'] <= prev['MA10'] and latest['MA5'] > latest['MA10'],
            'ma5_cross_down': prev['MA5'] >= prev['MA10'] and latest['MA5'] < latest['MA10'],
        },
        'macd': {
            'DIF': latest['DIF'], 'DEA': latest['DEA'], 'HIST': latest['MACD_HIST'],
            'above_zero': latest['DIF'] > 0 and latest['DEA'] > 0,
            'golden_cross': prev['DIF'] <= prev['DEA'] and latest['DIF'] > latest['DEA'],
            'dead_cross': prev['DIF'] >= prev['DEA'] and latest['DIF'] < latest['DEA'],
            'hist_expanding': latest['MACD_HIST'] > prev['MACD_HIST']
        },
        'boll': {
            'UP': latest['BOLL_UP'], 'MID': latest['BOLL_MID'], 'DOWN': latest['BOLL_DOWN'],
            'position': '上轨上方' if latest['Close'] > latest['BOLL_UP'] else 
                       '强势区' if latest['Close'] > latest['BOLL_MID'] else
                       '弱势区' if latest['Close'] > latest['BOLL_DOWN'] else '下轨下方'
        },
        'kdj': {
            'K': latest['K'], 'D': latest['D'], 'J': latest['J'],
            'status': '超买' if latest['J'] > 80 else '超卖' if latest['J'] < 20 else '中性',
            'golden_cross': prev['K'] <= prev['D'] and latest['K'] > latest['D'],
            'dead_cross': prev['K'] >= prev['D'] and latest['K'] < latest['D']
        }
    }
    
    # 波浪理论简单判断
    closes = data['Close'].values
    if len(closes) >= 20:
        trend_short = closes[-1] - closes[-6]
        trend_long = closes[-1] - closes[-21] if len(closes) >= 21 else 0
        
        if trend_long > 0:
            if trend_short > 0:
                result['wave'] = "可能处于上升浪(3浪或5浪)"
            else:
                result['wave'] = "可能处于调整浪(4浪)"
        else:
            if trend_short > 0:
                result['wave'] = "可能处于反弹浪(B浪)"
            else:
                result['wave'] = "可能处于下跌浪(A浪或C浪)"
    else:
        result['wave'] = "数据不足"
    
    return result

def print_analysis(result):
    """打印分析结果"""
    if result is None:
        print("数据不足，无法分析")
        return
    
    print(f"\n当前价格：{result['close']:.2f}")
    print(f"\n1. 波浪理论：{result['wave']}")
    
    print(f"\n2. 均线系统：")
    ma = result['ma']
    print(f"   MA5: {ma['MA5']:.2f} | MA10: {ma['MA10']:.2f} | MA20: {ma['MA20']:.2f} | MA60: {ma['MA60']:.2f}")
    print(f"   排列：{'多头排列' if ma['bullish'] else ('空头排列' if ma['bearish'] else '震荡')}")
    if ma['ma5_cross_up']: print(f"   ⚠️ MA5上穿MA10（金叉）")
    if ma['ma5_cross_down']: print(f"   ⚠️ MA5下穿MA10（死叉）")
    
    print(f"\n3. MACD：")
    macd = result['macd']
    print(f"   DIF: {macd['DIF']:.3f} | DEA: {macd['DEA']:.3f} | 柱: {macd['HIST']:.3f}")
    print(f"   位置：{'零轴上方' if macd['above_zero'] else '零轴下方'} | 柱体：{'扩大' if macd['hist_expanding'] else '缩小'}")
    if macd['golden_cross']: print(f"   ⚠️ MACD金叉")
    if macd['dead_cross']: print(f"   ⚠️ MACD死叉")
    
    print(f"\n4. 布林带：")
    boll = result['boll']
    print(f"   上轨: {boll['UP']:.2f} | 中轨: {boll['MID']:.2f} | 下轨: {boll['DOWN']:.2f}")
    print(f"   位置：{boll['position']}")
    
    print(f"\n5. KDJ：")
    kdj = result['kdj']
    print(f"   K: {kdj['K']:.1f} | D: {kdj['D']:.1f} | J: {kdj['J']:.1f}")
    print(f"   状态：{kdj['status']}")
    if kdj['golden_cross']: print(f"   ⚠️ KDJ金叉")
    if kdj['dead_cross']: print(f"   ⚠️ KDJ死叉")

def main():
    ticker = "600143.SS"
    
    print("=" * 60)
    print("金发科技（600143）技术分析报告")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取数据
    print("\n正在获取数据...")
    daily = yf.download(ticker, period="1y", interval="1d", progress=False)
    weekly = yf.download(ticker, period="3y", interval="1wk", progress=False)
    monthly = yf.download(ticker, period="5y", interval="1mo", progress=False)
    
    # 日线分析
    print("\n" + "=" * 60)
    print("【日线分析】")
    print("=" * 60)
    daily_result = analyze_period(daily, "日线")
    print_analysis(daily_result)
    
    # 周线分析
    print("\n" + "=" * 60)
    print("【周线分析】")
    print("=" * 60)
    weekly_result = analyze_period(weekly, "周线")
    print_analysis(weekly_result)
    
    # 月线分析
    print("\n" + "=" * 60)
    print("【月线分析】")
    print("=" * 60)
    monthly_result = analyze_period(monthly, "月线")
    print_analysis(monthly_result)
    
    # 综合判断
    print("\n" + "=" * 60)
    print("【综合判断】")
    print("=" * 60)
    
    if daily_result and weekly_result and monthly_result:
        d, w, m = daily_result, weekly_result, monthly_result
        
        # 支撑位和阻力位
        supports = sorted([d['boll']['DOWN'], d['boll']['MID'], w['boll']['DOWN']], reverse=True)
        resistances = sorted([d['boll']['UP'], w['boll']['UP'], w['boll']['MID']])
        
        print(f"\n📊 各周期技术面总结：")
        print(f"\n   日线：{'多头' if d['ma']['bullish'] else ('空头' if d['ma']['bearish'] else '震荡')} | "
              f"MACD{'强势' if d['macd']['above_zero'] else '弱势'} | KDJ{d['kdj']['status']}")
        print(f"   周线：{'多头' if w['ma']['bullish'] else ('空头' if w['ma']['bearish'] else '震荡')} | "
              f"MACD{'强势' if w['macd']['above_zero'] else '弱势'} | KDJ{w['kdj']['status']}")
        print(f"   月线：{'多头' if m['ma']['bullish'] else ('空头' if m['ma']['bearish'] else '震荡')} | "
              f"MACD{'强势' if m['macd']['above_zero'] else '弱势'} | KDJ{m['kdj']['status']}")
        
        print(f"\n🎯 关键支撑位：{', '.join([f'{s:.2f}' for s in supports])}")
        print(f"🎯 关键阻力位：{', '.join([f'{r:.2f}' for r in resistances])}")
        
        # 综合评分
        bullish_score = sum([
            d['ma']['bullish'], w['ma']['bullish'], m['ma']['bullish'],
            d['macd']['above_zero'], w['macd']['above_zero'], m['macd']['above_zero'],
            d['kdj']['status'] != '超买', w['kdj']['status'] != '超买'
        ])
        
        bearish_score = sum([
            d['ma']['bearish'], w['ma']['bearish'], m['ma']['bearish'],
            not d['macd']['above_zero'], not w['macd']['above_zero'], not m['macd']['above_zero'],
            d['kdj']['status'] == '超买', d['macd']['dead_cross']
        ])
        
        print(f"\n📋 操作建议：")
        if bullish_score >= 5:
            print(f"   建议：买入/持有")
            print(f"   理由：多周期指标向好，{bullish_score}/8项指标偏强")
        elif bearish_score >= 5:
            print(f"   建议：卖出/观望")
            print(f"   理由：多周期指标走弱，{bearish_score}/8项指标偏弱")
        else:
            print(f"   建议：观望")
            print(f"   理由：多空信号交织，等待趋势明朗（偏多:{bullish_score}, 偏空:{bearish_score}）")
        
        print(f"\n⚠️ 风险提示：")
        print(f"   1. 本分析仅供参考，不构成投资建议")
        print(f"   2. 股市有风险，投资需谨慎")
        print(f"   3. 波浪理论为主观判断，实际可能偏离")
        print(f"   4. 建议结合基本面和市场环境综合决策")

if __name__ == "__main__":
    main()
