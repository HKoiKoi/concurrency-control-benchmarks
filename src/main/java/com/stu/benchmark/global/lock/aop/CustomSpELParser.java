package com.stu.benchmark.global.lock.aop;

import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.StandardEvaluationContext;

public class CustomSpELParser {

	private CustomSpELParser() {
		throw new IllegalStateException("유틸리티 클래스입니다.");
	}

	public static Object getDynamicValue(String[] parameterNames, Object[] args, String name) {

		ExpressionParser parser = new SpelExpressionParser();
		StandardEvaluationContext context = new StandardEvaluationContext();

		for (int i = 0; i < parameterNames.length; i++) {
			context.setVariable(parameterNames[i], args[i]);
		}

		return parser.parseExpression(name).getValue(context, Object.class);
	}
}
