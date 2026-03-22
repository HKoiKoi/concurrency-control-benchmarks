package com.stu.benchmark.domain.enrollment.entity;

import java.time.LocalDateTime;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.DynamicInsert;

import com.stu.benchmark.domain.course.entity.Course;
import com.stu.benchmark.domain.student.entity.Student;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.experimental.FieldDefaults;

@Getter
@Entity
@DynamicInsert
@Table(
	name = "enrollment",
	uniqueConstraints = {
		@jakarta.persistence.UniqueConstraint(
			name = "uk_enrollment_student_id_course_id",
			columnNames = {"student_id", "course_id"}
		)
	}
)
@FieldDefaults(level = lombok.AccessLevel.PRIVATE)
@NoArgsConstructor(access = lombok.AccessLevel.PROTECTED)
public class Enrollment {

	@Id
	@Column(name = "enrollment_id")
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	Long id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "student_id", nullable = false)
	Student student;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "course_id", nullable = false)
	Course course;

	@CreationTimestamp
	@Column(nullable = false, updatable = false)
	LocalDateTime createdAt;

	@Builder
	public Enrollment(Student student, Course course) {
		this.student = student;
		this.course = course;
	}
}
