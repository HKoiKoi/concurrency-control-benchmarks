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
			// [저부하 상태]
			case PESSIMISTIC:
				// 트래픽이 '올라갈 때(UP)'만 신경쓰면 됨
				if (rho >= LockConstants.RHO_TH2_UP) {    // rho >= 0.34
					next = LockType.REDISSON;
				} else if (rho >= LockConstants.RHO_TH1_UP) {    // rho >= 0.24
					next = LockType.ZOOKEEPER;
				}

				break;

			// [중부하 상태]
			case ZOOKEEPER:
				// 더 심해지는지(UP), 완화되는지(DOWN) 모두 신경써야 함
				if (rho >= LockConstants.RHO_TH2_UP) {    // rho >= 0.34
					next = LockType.REDISSON;
				} else if (rho < LockConstants.RHO_TH1_DOWN) {    // rho < 0.22 (0.24보다 0.02 낮을 때 하강)
					next = LockType.PESSIMISTIC;
				}

				break;

			// [고부하 상태]
			case REDISSON:
				// 트래픽이 '내려갈 때(DOWN)'만 신경쓰면 됨
				if (rho < LockConstants.RHO_TH1_DOWN) {    // rho < 0.22
					next = LockType.PESSIMISTIC;
				} else if (rho < LockConstants.RHO_TH2_DOWN) {    // rho < 0.32 (0.34보다 0.02 낮을 때 하강)
					next = LockType.ZOOKEEPER;
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
