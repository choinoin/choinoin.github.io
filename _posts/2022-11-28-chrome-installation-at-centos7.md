---
title: "Centos7 에서 크롬 설치하기"
date: 2022-11-28 20:48:54 -0400
lastmod: 2022-11-28 20:48:54 -0400
categories: article
---
Centos 환경에서 chrome을 설치하기 위해선 먼저 설치파일인 rpm 파일이 필요하다.

rpm 파일은 wget 명령어를 통해 google 서버에서 받아올 수 있다.

```bash

[hostname]/home/username>wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

```

이를 통해 rpm 파일을 받아왔다면 yum 명령어를 통해 해당 프로그램을 설치할 수 있다.

```shell

[hostname]/home/username>yum localinstall google-chrome-stable_current_x86_64.rpm

```

이후 필요한 패키지의 설치를 묻는데 y를 입력한 후 엔터를 누르면 설치가 완료된다.
