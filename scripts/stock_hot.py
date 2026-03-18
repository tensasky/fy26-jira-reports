#!/usr/bin/env python3
"""
股票热点信息获取脚本
使用AKShare获取实时热点，推送到飞书
"""
import akshare as ak
import json
from datetime import datetime

def get_stock_hot():
    """获取股票热度榜"""
    try:
        # 获取A股热度榜
        hot_df = ak.stock_hot_rank_em()
        top10 = hot_df.head(10)
        
        result = []
        for _, row in top10.iterrows():
            result.append({
                "排名": int(row["排名"]),
                "股票代码": row["代码"],
                "股票名称": row["股票名称"],
                "最新价": row["最新价"],
                "涨跌幅": f"{row['涨跌幅']}%"
            })
        return result
    except Exception as e:
        return [{"error": str(e)}]

def get_stock_news(symbol="600688"):
    """获取个股新闻"""
    try:
        news_df = ak.stock_news_em(symbol=symbol)
        latest = news_df.head(5)
        
        result = []
        for _, row in latest.iterrows():
            result.append({
                "时间": row["发布时间"],
                "标题": row["新闻标题"],
                "来源": row.get("新闻来源", "")
            })
        return result
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    print("=== A股热度榜 TOP10 ===")
    hot = get_stock_hot()
    print(json.dumps(hot, ensure_ascii=False, indent=2))
    
    print("\n=== 上海石化(600688) 最新新闻 ===")
    news = get_stock_news("600688")
    print(json.dumps(news, ensure_ascii=False, indent=2))
