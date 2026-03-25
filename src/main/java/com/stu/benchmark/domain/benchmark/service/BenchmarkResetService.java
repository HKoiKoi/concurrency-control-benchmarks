package com.stu.benchmark.domain.benchmark.service;

import org.redisson.api.RKeys;
import org.redisson.api.RedissonClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import com.stu.benchmark.domain.benchmark.dto.BenchmarkResetResponse;
import com.stu.benchmark.domain.course.repository.CourseRepository;
import com.stu.benchmark.domain.enrollment.repository.EnrollmentRepository;
import com.stu.benchmark.global.lock.LockType;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class BenchmarkResetService {

	private final CourseRepository courseRepository;
	private final EnrollmentRepository enrollmentRepository;

	private final RedissonClient redissonClient;

	@Transactional
	public BenchmarkResetResponse resetBenchmark() {

		long currentEnrollmentCount = enrollmentRepository.count();
		long currentEnrolledCount = courseRepository.sumEnrolledCounts();

		// 데이터 초기화
		enrollmentRepository.deleteAllInBatch();
		courseRepository.resetAllEnrolledCounts();

		log.info("[Benchmark Reset] 수강 인원 0으로 변경 완료");
		log.info("[Benchmark Reset] 수강 이력 제거 완료 ({}건)", currentEnrollmentCount);

		// DB 커밋 이후에 Redis 잔여 락 강제 삭제 (트랜잭션 롤백 시 Redis 변경이 남는 불일치 방지)
		TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
			@Override
			public void afterCommit() {
				try {
					RKeys keys = redissonClient.getKeys();
					long totalDeletedLocks = 0;
					for (LockType lockType : LockType.values()) {
						totalDeletedLocks += keys.deleteByPattern(lockType.getPrefix() + "*");
					}
					log.info("[Benchmark Reset] Redis 락 제거 완료 ({}개)", totalDeletedLocks);
				} catch (Exception e) {
					log.error("[Benchmark Reset] Redis 락 제거 중 오류 발생. 잔여 락이 남아있을 수 있습니다.", e);
				}
			}
		});

		return new BenchmarkResetResponse(currentEnrolledCount, currentEnrollmentCount);
	}
}
