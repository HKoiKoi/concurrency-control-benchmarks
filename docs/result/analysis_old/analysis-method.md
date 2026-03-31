# 분석 방법

## Mean TPS

> nGrinder Result Summary의 `Mean TPS`와 `Peak TPS`를 활용합니다.

### Worst Mean TPS (최소)

- $n$번의 테스트 중 가장 낮은 `Mean TPS`

### Overall Mean TPS (평균)

- $n$번의 `Mean TPS`의 평균
- $\frac{\Sigma_{i=1}^{n}{\text{Mean TPS}}}{n}$

### Best Mean TPS (최대)

- $n$번의 테스트 중 가장 높은 `Mean TPS`

### Average Peak TPS (최대점 평균)

- $n$번의 테스트에서 기록된 `Peak TPS`의 평균
- $\frac{\Sigma_{i=1}^{n}{\text{Peak TPS}}}{n}$

---

## Mean Latency

> nGrinder 의 `Tests`, `Mean Test Time`을 활용합니다.

### Mean Latency

- 가중 평균
- $\text{Mean Latency}=\frac{\text{모든 사용자가 기다린 시간의 총합}}{\text{전체 사용자 수}}$
- $\mu_{total}=\frac{\Sigma_{i=1}^{k}{(n_i\cdot \mu_i)}}{\Sigma_{i=1}^{k}{n_i}}$

### Worst Mean Latency (가장 느림, 최대)

- $n$번의 테스트 중 가장 높은(느린) `Mean Latency`

### Overall Mean Latency (평균)

- $n$번의 `Mean Latency`의 평균
- $\frac{\Sigma_{i=1}^{n}{\text{Mean Latency}}}{n}$

### Best Mean Latency (가장 빠름, 최소)

- $n$번의 테스트 중 가장 낮은(빠른) `Mean Latency`

---

## p95 Latency

> nGrinder의 `Tests`, `Mean_Test_time`, `Test_Time_Standard_Deviation`을 활용합니다.

- nGrinder의 데이터를 바탕으로, 응답 시간의 롱테일(Long-tail) 특성을 반영한 **로그 정규 분포(Log-Normal Distribution) 모델을 적용하여 p95 지표를 통계적으로 추정**합니다.
  - 빠른 시간에 데이터가 볼록하게 몰려있고, 느린 시간으로 꼬리가 길게 늘어지는 **로그 정규 분포**가 컴퓨터 공학에서 네트워크나 디스크 I/O 지연 시간을 모델링하기 적합하기에 채용합니다.

### $p95$ 추정을 위한 계산 공식

- $n_i$: `Tests` (요청 건수)
- $\mu_i$: `Mean_Test_Time` (평균 지연 시간)
- $\sigma_i$: `Test_Time_Standard_Deviation` (표준편차)

#### 전체 가중 평균(Overall Weighted Mean) 구하기

- 요청 건수($n_i$)가 많은 구간에 더 높은 가중치 주어야 함(총합 테스트 건수로 전체 시간의 합을 나누는 개념)
  - $\mu_{total}=\frac{\Sigma_{i=1}^{k}{(n_i\cdot \mu_i)}}{\Sigma_{i=1}^{k}{n_i}}$

#### 전체 결합 분산(Poolead Variance) 구하기

- 통계학의 '제곱의 평균($E[X^2]$)' 공식 이용해 분산 병합
  - 각 행의 제곱 평균 구함: $E[X_i^2]=\sigma_i^2 + \mu_i^2$
  - 전체 제곱 평균을 가중합으로 구함: $E[X^2]_{total}=\frac{\Sigma_{i=1}^{k}{(n_i\cdot E[X_i^2])}}{\Sigma_{i=1}^{k}{n_i}}$
  - 최종 전체 분산($\sigma_{total}^2$) 도출: $\sigma_{total}^2=E[X^2]_{total} - (\mu_{total})^2$

#### 일반 통계를 Log-Normal 파라미터로 변환

- 앞서 구한 전체 평균($m = \mu_{total}$)과 전체 분산($v=\sigma_{total}^2$)을 이용해 로그 정규 분포 파라미터($\mu_{log}, \sigma_{log}$)로 매핑
  - $\sigma_{log}=\sqrt{ln(1+\frac{v}{m^2})}$
  - $\mu_{log}=ln(m) - \frac{\sigma_{log}^2}{2}$

#### 최종 p95 계산

- 로그 정규 분포의 누적 분포 함수(CDF)의 역함수를 이용하여 시간 값이 가장 큰(오래 걸린) 상위 5%(0.95; 높은 시간) 지점 찾음
- Z-스코어($Z_{0.95} \approx 1.64485$)를 사용하여 95% 경계선을 찾음
  - $$p95 = \exp(\underbrace{\mu_{log}}_{출발점} + \underbrace{1.64485 \cdot \sigma_{log}}_{이동 거리})$$

---

## 표준편차($\sigma$) 및 $2\sigma$ 신뢰 구간 안정성

- 전체 평균인 $\mu_{total}$ `Overall Mean Latency` 결과 활용
- $n_i$: `Tests` (요청 건수)
- $\mu_i$: `Mean_Test_Time` (평균 지연 시간)
- $\sigma_i$: `Test_Time_Standard_Deviation` (표준편차)
- $N$: 전체 테스트 건수의 합계 ($\Sigma_{i=1}^kn_i$)

### 표준편차($\sigma$)

#### $\mu_{total}$을 가져오기

#### 그룹 내 제곱합($SS_{within}$) 구하기

- $SS_{within} = \Sigma_{i=1}^{k}(n_i-1)\sigma_i^2$

#### 그룹 간 제곱합($SS_{between}$)

- $SS_{between}=\Sigma_{i=1}^{k}n_i(\mu_i-\mu_{total})^2$

#### 최종 통합 표준편차($\sigma_{total}$)

- $\sigma_{total}=\sqrt{\frac{SS_{within} + SS_{between}}{N-1}}$

### $2\sigma$ 신뢰 구간

$$[\mu_{total} - 2\sigma_{total}, \mu_{total} + 2\sigma_{total}]$$
