---
title: "NoinML type 설명(Model)"
date: 2021-05-24 10:00:00 -0400
lastmod: 2022-11-28 21:04:05 -0400
categories: article
---
개발중인 NoinML의 data type에 대한 설명글이다.

NoinML에서 필요한 모든 data를 감싸는 wrapper 역할을 한다 생각하면 된다.

이하 Model data type의 정의다.

```c
typedef struct Model {

	cudnnHandle_t cudnnHandle;

	char *name;

	int NLayer;

	Layer *iLayer;
	Layer *fLayer;

	Layer *Layers;

	LayerData **datas;
} Model;
```

가장 먼저 설명할 것은 cudnnHandle이다.

cudnnHandle은 cudnn API를 사용하기 위해 꼭 필요한 data이며, 해당 Handle을 이햐의 Layer 내 pointer에 연결하여 Layer 수준에서 cudnn 함수를 사용할 때에 활용된다.


