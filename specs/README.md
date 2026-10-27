# 切片规格

`specs/slices/{SLICE_ID}/` 是每个实现切片的事实源。canonical 切片必须包含：

- `slice.yaml`：切片元数据和依赖。
- `contract.md`：验收标准、测试边界、依赖与 Mock 策略。

新增切片 ID：

```text
ERP-SLICE-{DOMAIN}-{NNN}
```

域白名单：

```text
PRODUCT, ORD, B2C, IMS, ASS, FIN, PUR, PLAT
```

