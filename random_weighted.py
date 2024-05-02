import random 
sampleList = [Bronze, Silver, Gold, Platinum]
 
randomList = random.choices(
  sampleList, weights=(40, 30, 20, 10))
 


print(randomList)