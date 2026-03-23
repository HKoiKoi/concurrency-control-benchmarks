package com.stu.benchmark.domain.enrollment.facade;

import java.util.concurrent.TimeUnit;

import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.stereotype.Component;

import com.stu.benchmark.domain.enrollment.dto.EnrollmentCreateRequest;
import com.stu.benchmark.domain.enrollment.service.EnrollmentService;
import com.stu.benchmark.global.exception.LockAcquisitionException;
import com.stu.benchmark.global.lock.LockType;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class PubSubLockFacade {

	private final RedissonClient redissonClient;

	private final EnrollmentService enrollmentService;

	/**
	 * [Case 3: Pub/Sub Lock] 강의 엔터티에 대해 Pub/Sub Lock을 적용하여 동시성 문제를 방지하는 수강신청
	 */
	public void enrollWithPubSubLock(EnrollmentCreateRequest request) {

		String lockKey = LockType.REDISSON.generateKey(request.courseId());
		RLock lock = redissonClient.getLock(lockKey);

		boolean available;

		try {
			// 락 획득 시도
			// waitTime: 락 획득을 시도하는 최대 대기 시간 (5초)
			// leaseTime: 락이 자동으로 해제되는 시간 (3초)
			// TODO: 테스트 할 때 waitTime과 leaseTime을 조정하여 성능 평가(e.g., waitTime 3~10초, leaseTime 2~5초, 워치독(-1))
			available = lock.tryLock(5, 3, TimeUnit.SECONDS);
		} catch (InterruptedException e) {
			Thread.currentThread().interrupt();
			throw new LockAcquisitionException("Pub/Sub Lock 대기 중 스레드 인터럽트 발생", e);
		}

		if (!available) {
			log.error("[Pub/Sub Lock] 락 획득 타임아웃. courseId: {}, studentId: {}",
				request.courseId(), request.studentId());
			throw new LockAcquisitionException("락 획득 대기 시간 초과");
		}
		try {
			enrollmentService.enroll(request);
		} finally {
			// 락 해제
			if (lock.isLocked() && lock.isHeldByCurrentThread()) {
				lock.unlock();
			}
		}
	}
}
