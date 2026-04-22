package com.stu.benchmark.domain.enrollment.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.stu.benchmark.domain.enrollment.dto.EnrollmentCreateRequest;
import com.stu.benchmark.domain.enrollment.facade.PubSubLockFacade;
import com.stu.benchmark.domain.enrollment.facade.SpinLockFacade;
import com.stu.benchmark.domain.enrollment.facade.ZookeeperLockFacade;
import com.stu.benchmark.domain.enrollment.service.EnrollmentService;
import com.stu.benchmark.domain.enrollment.service.EnrollmentServiceV2;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequiredArgsConstructor
@RequestMapping("/v1/enrollments")
public class EnrollmentController {

	private final SpinLockFacade spinLockFacade;
	private final PubSubLockFacade pubSubLockFacade;
	private final ZookeeperLockFacade zookeeperLockFacade;

	private final EnrollmentService enrollmentService;
	private final EnrollmentServiceV2 enrollmentServiceV2;

	/**
	 * Baseline: No Lock API
	 */
	@PostMapping("/no-lock")
	public ResponseEntity<String> enrollWithNoLock(
		@Valid @RequestBody EnrollmentCreateRequest request
	) {
		enrollmentService.enroll(request);
		return ResponseEntity.ok("[Baseline] 수강신청이 성공적으로 완료되었습니다.");
	}

	/**
	 * Case 1: Pessimistic Lock API
	 */
	@PostMapping("/pessimistic-lock")
	public ResponseEntity<String> enrollWithPessimisticLock(
		@Valid @RequestBody EnrollmentCreateRequest request
	) {
		enrollmentService.enrollWithPessimisticLock(request);
		return ResponseEntity.ok("[Case 1: Pessimistic Lock] 수강신청이 성공적으로 완료되었습니다.");
	}

	/**
	 * Case 2: Spin Lock API
	 */
	@PostMapping("/spin-lock")
	public ResponseEntity<String> enrollWithSpinLock(
		@Valid @RequestBody EnrollmentCreateRequest request
	) {
		spinLockFacade.enrollWithSpinLock(request);
		return ResponseEntity.ok("[Case 2: Spin Lock] 수강신청이 성공적으로 완료되었습니다.");
	}

	/**
	 * Case 3: Pub/Sub Lock API
	 */
	@PostMapping("/pub-sub-lock")
	public ResponseEntity<String> enrollWithPubSubLock(
		@Valid @RequestBody EnrollmentCreateRequest request
	) {
		pubSubLockFacade.enrollWithPubSubLock(request);
		return ResponseEntity.ok("[Case 3: Pub/Sub Lock] 수강신청이 성공적으로 완료되었습니다.");
	}

	/**
	 * Case 4: Zookeeper Lock API
	 */
	@PostMapping("/zookeeper-lock")
	public ResponseEntity<String> enrollWithZookeeperLock(
		@Valid @RequestBody EnrollmentCreateRequest request
	) {
		zookeeperLockFacade.enrollWithZookeeperLock(request);
		return ResponseEntity.ok("[Case 4: Zookeeper Lock] 수강신청이 성공적으로 완료되었습니다.");
	}

	/**
	 * Case 5: Adaptive Lock API (V2)
	 * 실시간 부하에 따라 최적의 락(Pessimistic Lock, Zookeeper Lock, Redisson Lock)을 동적으로 선택하는 수강신청
	 */
	@PostMapping("/adaptive-lock")
	public ResponseEntity<String> enrollWithAdaptiveLock(
		@Valid @RequestBody EnrollmentCreateRequest request
	) {
		enrollmentServiceV2.enroll(request);
		return ResponseEntity.ok("[Case 5: Adaptive Lock V2] 수강신청이 성공적으로 완료되었습니다.");
	}
}
