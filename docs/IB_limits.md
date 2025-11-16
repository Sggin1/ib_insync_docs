# IB API Data Limits & Analysis Dataset Cheat Sheet

## 📊 IB API Constraints

### Request Limits
- **Max simultaneous requests**: 50 (practical: 5-10)
- **Pacing violations** (≤30 sec bars):
  - No identical requests within 15 seconds
  - Max 6 requests per contract within 2 seconds  
  - Max 60 requests per 10 minutes
- **Max bars per request**: ~2,000 bars
- **Historical data age**: 6 months for ≤30 sec bars
 **TICKS**: 1000 TICKS max download ( extremly low ) so no need to request , just Start Real time data and record from there to create bars and combine with historiucal, this gives minimal delays in data.
 


 (Safe Limits)
```
5-second:   6 days    (518,400 bars) - 12 requests (dual-call method)
  Sunday 6pm-Friday 5pm, 2 requesst per day
  use UTC but market open 6pm EST Sunday- <0000  2nd request 0000- <1700
1-minute:   15 days   (21,600 bars)  - 15 requests  
15-minute:  45 days   (4,320 bars)   - 3 requests
1-hour:     90 days   (2,160 bars)   - 2 requests
Daily:      180 days  (180 bars)     - 1 request
Total: 33 requests (well within 10-min limit)
```


## ⚡ Download Strategy
0. TEST NEW METHOD :  GET  DATA UNTIL FAIL. REPEAT NEXT TIME BLOCK UNTIL DESIRED DATA REACHED, CAUTION REQUESTS.
1. **Use dual-call method** for 5-second data (proven: 2 calls per day)
2. **Fallback to 4-hour blocks** if dual-call fails (48 requests for 4 days)
3. **Batch by timeframe** (all 5s, then all 1m, etc.)
4. **Stagger requests** (2-3 second delays)
5. **Monitor pacing** (track request count/time)
6. **Aggregate up** (5s→1m→15m→1h→daily) to reduce API calls

## 🚨 Key Considerations
- **Volume data**: IB historical ≠ real-time (known issue)
- **Weekend data**: Limited to evening sessions
- **Futures expiry**: Data available 2 years post-expiry
- **Rate limiting**: Soft throttling vs hard disconnects
- **Best practice**: Download incrementally, not bulk historical

## 💡 Implementation Tips

- Monitor API response times
- Implement exponential backoff on errors
- Cache aggressively to minimize re-requests
