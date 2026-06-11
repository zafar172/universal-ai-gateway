import httpx,time
time.sleep(4)
b="http://127.0.0.1:8080"
tk=httpx.post(f"{b}/login",json={"email":"validation@test.local","password":"SuperSecret123"}).json()["access_token"]
h={"Authorization":f"Bearer {tk}"}
cid=httpx.post(f"{b}/v1/conversations",headers=h).json()["conversation_id"]
httpx.post(f"{b}/v1/conversations/{cid}/chat",headers=h,json={"messages":[{"role":"user","content":"Capital?"}],"routing_strategy":"lowest_cost"})
httpx.post(f"{b}/v1/conversations/{cid}/chat",headers=h,json={"messages":[{"role":"user","content":"Pop?"}],"routing_strategy":"lowest_cost"})
hist=httpx.get(f"{b}/v1/conversations/{cid}",headers=h).json()["messages"]
print("\\n[QWEN] PHASE 2 VALIDATED! SUCCESS!\\n" if len(hist)>=4 else f"\\n[QWEN] FAILED: {len(hist)}\\n")
