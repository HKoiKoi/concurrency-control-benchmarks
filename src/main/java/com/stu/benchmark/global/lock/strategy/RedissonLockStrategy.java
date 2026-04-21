package com.stu.benchmark.global.lock.strategy;

import java.util.concurrent.TimeUnit;

import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.stereotype.Component;

import com.stu.benchmark.global.lock.DistributedLock;
import com.stu.benchmark.global.lock.LockType;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class RedissonLockStrategy implements DistributedLock {

	private final RedissonClient redissonClient;

	@Override
	public boolean tryLock(String key, long waitTime, long leaseTime, TimeUnit unit) {

		RLock lock = redissonClient.getLock(key);

		try {
			return lock.tryLock(waitTime, leaseTime, unit);
		} catch (InterruptedException e) {
			log.error("[Redisson Lock] 락 획득 대기 중 인터럽트 발생. lockKey: {}", key, e);
			Thread.currentThread().interrupt();
			return false;
		}
	}

	@Override
	public void unlock(String key) {

		RLock lock = redissonClient.getLock(key);

		if (lock.isHeldByCurrentThread()) {
			lock.unlock();
		} else {
			log.warn("[Redisson Lock] 현재 스레드가 보유하지 않은 락 해제 시도. lockKey: {}", key);
		}
	}

	@Override
	public LockType getLockType() {
		return LockType.REDISSON;
	}
}
