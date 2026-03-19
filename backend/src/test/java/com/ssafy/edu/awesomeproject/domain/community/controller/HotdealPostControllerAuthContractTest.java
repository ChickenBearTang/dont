package com.ssafy.edu.awesomeproject.domain.community.controller;

import static org.assertj.core.api.Assertions.assertThat;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.Arrays;
import org.junit.jupiter.api.Test;

class HotdealPostControllerAuthContractTest {

    @Test
    void createAndUpdateEndpointsUseCurrentUserIdArgumentResolver() {
        Method createMethod = findMethod("create");
        Method updateMethod = findMethod("update");

        assertThat(hasCurrentUserIdParameter(createMethod)).isTrue();
        assertThat(hasCurrentUserIdParameter(updateMethod)).isTrue();
    }

    @Test
    void createAndUpdateEndpointsDoNotUseRequestHeaderAuthorizationParsing() {
        Method createMethod = findMethod("create");
        Method updateMethod = findMethod("update");

        assertThat(hasAuthorizationHeaderParameter(createMethod)).isFalse();
        assertThat(hasAuthorizationHeaderParameter(updateMethod)).isFalse();
    }

    private Method findMethod(String methodName) {
        return Arrays.stream(HotdealPostController.class.getDeclaredMethods())
                .filter(method -> method.getName().equals(methodName))
                .findFirst()
                .orElseThrow();
    }

    private boolean hasCurrentUserIdParameter(Method method) {
        return Arrays.stream(method.getParameters())
                .map(Parameter::getAnnotations)
                .flatMap(Arrays::stream)
                .map(Annotation::annotationType)
                .anyMatch(CurrentUserId.class::equals);
    }

    private boolean hasAuthorizationHeaderParameter(Method method) {
        return Arrays.stream(method.getParameters())
                .map(Parameter::getAnnotations)
                .flatMap(Arrays::stream)
                .map(Annotation::annotationType)
                .anyMatch(annotationType -> annotationType.getSimpleName().equals("RequestHeader"));
    }
}
