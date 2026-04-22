package com.stu.benchmark.domain.enrollment.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.stu.benchmark.domain.course.entity.Course;
import com.stu.benchmark.domain.course.repository.CourseRepository;
import com.stu.benchmark.domain.enrollment.dto.EnrollmentCreateRequest;
import com.stu.benchmark.domain.enrollment.entity.Enrollment;
import com.stu.benchmark.domain.enrollment.repository.EnrollmentRepository;
import com.stu.benchmark.domain.student.entity.Student;
import com.stu.benchmark.domain.student.repository.StudentRepository;
import com.stu.benchmark.global.lock.LockContextHolder;
import com.stu.benchmark.global.lock.LockType;
import com.stu.benchmark.global.lock.aop.AdaptiveLock;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class EnrollmentServiceV2 {

	private final CourseRepository courseRepository;
	private final StudentRepository studentRepository;
	private final EnrollmentRepository enrollmentRepository;

	/**
	 * [Adaptive Framework V2] 모든 락 전략을 수용하는 통합 수강신청 메서드
	 */
	@Transactional
	@AdaptiveLock(key = "#request.courseId()")
	public void enroll(EnrollmentCreateRequest request) {

		// 학생, 강의 조회
		Student student = studentRepository.findById(request.studentId())
			.orElseThrow(() -> new IllegalArgumentException("학생이 존재하지 않습니다."));
		Course course;

		if (LockContextHolder.get() == LockType.PESSIMISTIC) {
			course = courseRepository.findByIdWithPessimisticLock(request.courseId())
				.orElseThrow(() -> new IllegalArgumentException("강의가 존재하지 않습니다."));
		} else {
			course = courseRepository.findById(request.courseId())
				.orElseThrow(() -> new IllegalArgumentException("강의가 존재하지 않습니다."));
		}

		// 수강신청
		if (enrollmentRepository.existsByStudentIdAndCourseId(student.getId(), course.getId())) {
			throw new IllegalStateException("해당 강의는 이미 수강신청되었습니다.");
		}

		course.increaseEnrolledCount();

		// 수강신청 정보 저장
		enrollmentRepository.save(
			Enrollment.builder()
				.studentId(student.getId())
				.courseId(course.getId())
				.build()
		);
	}
}
