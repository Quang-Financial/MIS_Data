import datetime as dt, json, hashlib, math, pathlib, urllib.request
D=86400000
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=ROOT/'data/btcusd-bitstamp.json'
M=ROOT/'data/manifest.json'
def validate(bars,today):
    if not bars or bars[0]['t']!=1313625600000: raise ValueError('Missing original history')
    for i,b in enumerate(bars):
        t,o,h,l,c=(b[k] for k in ('t','o','h','l','c'))
        if not all(math.isfinite(x) for x in (t,o,h,l,c)) or t%D or t>=today or l<=0 or h<max(o,l,c) or l>min(o,c): raise ValueError('Invalid OHLC')
        if i and t-bars[i-1]['t']!=D: raise ValueError('Gap or duplicate')
def main():
    today=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)//D*D
    if P.exists():
        old=json.loads(P.read_text())
        if old['source']!='Bitstamp BTC/USD': raise ValueError('Wrong source')
        bars=old['bars']; validate(bars,today)
        start=bars[-1]['t']+D
    else:
        bars=[]
        start=1313625600000
    while start<today:
        end=min(start+999*D,today-D)
        url=f'https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=86400&limit=1000&start={start//1000}&end={end//1000}&exclude_current_candle=true'
        with urllib.request.urlopen(url,timeout=30) as r: rows=json.load(r)['data']['ohlc']
        batch=sorted([dict(t=int(x['timestamp'])*1000,o=float(x['open']),h=float(x['high']),l=float(x['low']),c=float(x['close'])) for x in rows if start<=int(x['timestamp'])*1000<=end],key=lambda x:x['t'])
        if len(batch)!=(end-start)//D+1: raise ValueError('Incomplete API batch')
        bars.extend(batch); start=end+D
    validate(bars,today)
    if bars[-1]['t']!=today-D: raise ValueError('Latest completed candle missing')
    raw=json.dumps(dict(source='Bitstamp BTC/USD',bars=bars),separators=(',',':'),allow_nan=False).encode()
    manifest=dict(schema=1,source='Bitstamp BTC/USD',path='data/btcusd-bitstamp.json',sha256=hashlib.sha256(raw).hexdigest(),days=len(bars),first=bars[0]['t'],last=bars[-1]['t'])
    P.parent.mkdir(parents=True,exist_ok=True)
    P.write_bytes(raw); M.write_text(json.dumps(manifest,separators=(',',':'))+'\n')
if __name__=='__main__': main()
