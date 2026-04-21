package com.stu.benchmark.global.lock;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.stereotype.Component;

@Component
public class LockStrategyFactory {

	private final Map<LockType, DistributedLock> strategies;

	public LockStrategyFactory(List<DistributedLock> lockStrategies) {
		this.strategies = lockStrategies.stream()
			.collect(Collectors.toMap(
				DistributedLock::getLockType,
				Function.identity()
			));
	}

	public DistributedLock getStrategy(LockType lockType) throws IllegalAccessException {

		DistributedLock strategy = strategies.get(lockType);

		if (strategy == null) {
			throw new IllegalAccessException("지원하지 않는 락 타입입니다: " + lockType);
		}

		return strategy;
	}
}
