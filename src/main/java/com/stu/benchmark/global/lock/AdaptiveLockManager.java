package com.stu.benchmark.global.lock;

import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class AdaptiveLockManager {

	private final LockStrategyFactory lockStrategyFactory;

	private LockType currentLockType = LockType.PESSIMISTIC;

	public DistributedLock determineLockStrategy(double currentTps) throws IllegalAccessException {

		double rho = currentTps / LockConstants.SYSTEM_CAPACITY_MU;
		LockType nextLockType = currentLockType;

		if (rho < LockConstants.RHO_THRESHOLD_LOW) {
			nextLockType = LockType.PESSIMISTIC;
		} else if (rho >= LockConstants.RHO_THRESHOLD_LOW && rho < LockConstants.RHO_THRESHOLD_HIGH) {
			nextLockType = LockType.ZOOKEEPER;
		} else if (rho >= LockConstants.RHO_THRESHOLD_HIGH) {
			nextLockType = LockType.REDISSON;
		}

		if (this.currentLockType != nextLockType) {
			log.info(
				"[AdaptiveLock] 시스템 상태 전이 발생! TPS: {}, 이용률(rho): {}, 전환: {} -> {}",
				currentTps, String.format("%.2f", rho), this.currentLockType, nextLockType
			);
			this.currentLockType = nextLockType;
		}

		return lockStrategyFactory.getStrategy(nextLockType);
	}

	public LockType getCurrentLockType() {
		return this.currentLockType;
	}
}
