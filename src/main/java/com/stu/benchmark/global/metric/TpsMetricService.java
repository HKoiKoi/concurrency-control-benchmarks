package com.stu.benchmark.global.metric;

import java.util.concurrent.atomic.LongAdder;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class TpsMetricService {

	// 멀티스레드 환경에서 경합 오버헤드가 적은 LongAdder 사용
	private final LongAdder requestCounter = new LongAdder();

	/**
	 * -- GETTER --
	 *  현재 측정된 TPS 반환
	 *  다른 스레드(AOP)에서 항상 최신 값 읽어오도록 volatile 선언
	 */
	@Getter
	private volatile double currentTps = 0.0;

	/**
	 * EMA 평활 계수 (0 ~ 1)
	 * 0.5: 최신 데이터(이번 1초) 50%, 과거 데이터 50%를 반영
	 */
	private static final double ALPHA = 0.5;

	/**
	 * API 호출 시 카운트 증가 (AOP에서 호출)
	 */
	public void recordRequest() {
		requestCounter.increment();
	}

	/**
	 * 1초마다 실행되어 누적된 요청 수를 TPS로 저장하고 카운터 초기화
	 */
	@Scheduled(fixedRate = 1000)
	public void calculateAndResetTps() {

		long count = requestCounter.sumThenReset();

		// EMA(지수 이동 평균) 적용
		// 공식: (새로운 측정값 * 가중치) + (기존 평균 * (1 - 가중치))
		this.currentTps = (count * ALPHA) + (this.currentTps * (1 - ALPHA));

		// 소수점 낭비를 막기 위해 0.1 미만은 0으로 취급
		if (this.currentTps < 0.1) {
			this.currentTps = 0.0;
		}

		// TPS가 0이 아닐 때만 로그를 찍어 확인
		if (this.currentTps > 0) {
			log.debug("[Metric] 실시간 TPS: {}", String.format("%.2f", this.currentTps));
		}
	}
}
