package com.stu.benchmark.global.lock;

import org.springframework.stereotype.Component;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class AdaptiveLockManager {

	private final LockStrategyFactory lockStrategyFactory;

	@Getter
	private LockType currentLockType = LockType.PESSIMISTIC;

	public DistributedLock determineLockStrategy(double currentTps) throws IllegalAccessException {

		double rho = currentTps / LockConstants.SYSTEM_CAPACITY_MU;
		LockType nextLockType = currentLockType;

		switch (currentLockType) {
			// [저부하 상태]
			case PESSIMISTIC:
				// 트래픽이 '올라갈 때(UP)'만 신경쓰면 됨
				if (rho >= LockConstants.RHO_TH2_UP) {    // rho >= 0.34
					nextLockType = LockType.REDISSON;
				} else if (rho >= LockConstants.RHO_TH1_UP) {    // rho >= 0.24
					nextLockType = LockType.ZOOKEEPER;
				}

				break;

			// [중부하 상태]
			case ZOOKEEPER:
				// 더 심해지는지(UP), 완화되는지(DOWN) 모두 신경써야 함
				if (rho >= LockConstants.RHO_TH2_UP) {    // rho >= 0.34
					nextLockType = LockType.REDISSON;
				} else if (rho < LockConstants.RHO_TH1_DOWN) {    // rho < 0.22 (0.24보다 0.02 낮을 때 하강)
					nextLockType = LockType.PESSIMISTIC;
				}

				break;

			// [고부하 상태]
			case REDISSON:
				// 트래픽이 '내려갈 때(DOWN)'만 신경쓰면 됨
				if (rho < LockConstants.RHO_TH1_DOWN) {    // rho < 0.22
					nextLockType = LockType.PESSIMISTIC;
				} else if (rho < LockConstants.RHO_TH2_DOWN) {    // rho < 0.32 (0.34보다 0.02 낮을 때 하강)
					nextLockType = LockType.ZOOKEEPER;
				}

				break;

			default:
				break;
		}

		if (this.currentLockType != nextLockType) {
			log.info(
				"[AdaptiveLock Transition] TPS: {}, 이용률: {}, 전환: {} -> {}",
				String.format("%.2f", currentTps),
				String.format("%.2f", rho),
				this.currentLockType,
				nextLockType
			);

			this.currentLockType = nextLockType;
		}

		return lockStrategyFactory.getStrategy(nextLockType);
	}
}
