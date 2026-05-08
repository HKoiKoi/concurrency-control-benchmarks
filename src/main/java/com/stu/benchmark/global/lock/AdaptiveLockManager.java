package com.stu.benchmark.global.lock;

import java.util.concurrent.atomic.AtomicReference;

import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class AdaptiveLockManager {

	private final LockStrategyFactory lockStrategyFactory;

	// 멀티스레드 환경에서 동시 읽기·쓰기 경합을 방지하기 위해 AtomicReference 사용
	private final AtomicReference<LockType> currentLockType = new AtomicReference<>(LockType.PESSIMISTIC);

	public LockType getCurrentLockType() {
		return currentLockType.get();
	}

	public DistributedLock determineLockStrategy(double currentTps) {

		double rho = currentTps / LockConstants.SYSTEM_CAPACITY_MU;

		LockType current = currentLockType.get();
		LockType next = current;

		switch (current) {
			// [임계 부하 구간]
			case PESSIMISTIC:
				// 트래픽 상승: 상향 임계점(0.24) 돌파 시 Pub/Sub(Redisson) 전환
				if (rho >= LockConstants.RHO_TH1_UP) {    // rho >= 0.24
					next = LockType.REDISSON;
				}

				break;

			// [과부하 & 포화 부하 구간]
			case REDISSON:
				// 트래픽 하강: 하향 임계점(0.22) 미만 시 Pessimistic 복귀 (히스테리시스 적용)
				if (rho < LockConstants.RHO_TH1_DOWN) {    // rho < 0.22
					next = LockType.PESSIMISTIC;
				}

				break;

			default:
				break;
		}

		// CAS(Compare-And-Swap)로 현재 상태를 원자적으로 갱신
		if (current != next && currentLockType.compareAndSet(current, next)) {
			log.info(
				"[AdaptiveLock Transition] TPS: {}, 이용률: {}, 전환: {} -> {}",
				String.format("%.2f", currentTps),
				String.format("%.2f", rho),
				current,
				next
			);
		}

		return lockStrategyFactory.getStrategy(next);
	}
}
