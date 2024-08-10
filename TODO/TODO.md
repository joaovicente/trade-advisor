# Optimisation strategy as of 2024-08-08

Current strategy

Buys when:
* bb-bot is crossed upwards and RSI below 40

Sells when:
* bb-mid hat (^) shape
* or price boes below bb-low

Optimisation opportunities below

## 1. Tolerance to low magnitude and sustain of bb-low crossover

sell_upon_bb_low_crossover(magnitude_tolerance, days_tolerance)

![alt text](image.png)
[ ] FIXME: AMZN is selling due to bb-mid-inflection (not bb-low downwards crossover) - consider measuring gradient between n days and today 

![alt text](image-2.png)
![alt text](image-3.png)
![alt text](image-4.png)
![alt text](image-5.png)
![alt text](image-6.png)
![alt text](image-7.png)

## 2. Tolerance to bb-mid inflection when variance of price is low (measurable in inflection downswing?) 

sell_upon_on_bb_mid_hat_inflection()

![alt text](image-1.png)

## 3. Analyse why COST did not trigger buy

![alt text](image-8.png)