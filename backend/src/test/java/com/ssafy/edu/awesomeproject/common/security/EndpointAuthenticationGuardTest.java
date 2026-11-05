package com.ssafy.edu.awesomeproject.common.security;

import static org.assertj.core.api.Assertions.assertThat;

import com.ssafy.edu.awesomeproject.common.annotation.AdminOnly;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.Set;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.core.type.filter.AnnotationTypeFilter;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 이 서비스의 인증은 "메서드가 켜는" 방식이다. CurrentUserInterceptor 는 @CurrentUserId 파라미터나 @AdminOnly 가 있는
 * 핸들러에서만 토큰을 검사하고, 그런 표시가 없는 핸들러는 누구나 부를 수 있다 (실패했을 때 열리는 구조).
 *
 * <p>그래서 새 엔드포인트에서 표시를 빠뜨리면 조용히 공개된다. 실제로 `GET /users/{id}/finance-profile` 과 `/dummy/*` 가
 * 그렇게 인증 없이 열려 있었다. 이 테스트는 로그인 없이 부를 수 있는 엔드포인트를 아래 목록으로 못 박아서, 목록에 없는
 * 공개 엔드포인트가 생기면 빌드가 깨지게 한다. 정말 공개해야 하는 엔드포인트라면 이유를 생각하고 목록에 추가한다.
 *
 * <p>CurrentUserInterceptor#requiresAuthentication 과 같은 조건으로 판정한다.
 */
class EndpointAuthenticationGuardTest {

    /** 로그인 없이 부를 수 있는 엔드포인트 (컨트롤러 단순 이름#메서드). */
    private static final Set<String> PUBLIC_ENDPOINTS =
            Set.of(
                    // 로그인 전에 쓰는 것들
                    "AuthController#getCohorts",
                    "AuthController#checkEmail",
                    "AuthController#sendEmailVerificationCode",
                    "AuthController#confirmEmailVerificationCode",
                    "AuthController#requestPasswordReset",
                    "AuthController#confirmPasswordReset",
                    "AuthController#signup",
                    "AuthController#login",
                    "AuthController#reissue",
                    "AuthController#logout",
                    // 핫딜·토론 상세는 읽기 전용으로 공개돼 있다 (작성자 닉네임/이미지와 글 내용만 담는다). 다른 글 종류의
                    // 상세는 로그인이 필요해서 의도인지 확인이 필요하다.
                    "HotdealPostController#detail",
                    "PollPostController#detail");

    @Test
    void everyEndpointRequiresLoginUnlessItIsListedAsPublic() throws Exception {
        Set<String> actuallyPublic = new TreeSet<>();
        int handlers = 0;

        ClassPathScanningCandidateComponentProvider scanner =
                new ClassPathScanningCandidateComponentProvider(false);
        scanner.addIncludeFilter(new AnnotationTypeFilter(RestController.class));

        for (BeanDefinition definition : scanner.findCandidateComponents("com.ssafy.edu.awesomeproject")) {
            Class<?> controller = Class.forName(definition.getBeanClassName());
            for (Method method : controller.getDeclaredMethods()) {
                if (!AnnotatedElementUtils.hasAnnotation(method, RequestMapping.class)) {
                    continue;
                }
                handlers++;
                if (!requiresAuthentication(controller, method)) {
                    actuallyPublic.add(controller.getSimpleName() + "#" + method.getName());
                }
            }
        }

        assertThat(handlers).as("컨트롤러를 못 찾으면 이 테스트는 아무것도 지키지 못한다").isGreaterThan(50);
        assertThat(actuallyPublic)
                .as("인증 표시(@CurrentUserId/@AdminOnly)가 없는데 공개 목록에도 없는 엔드포인트")
                .isSubsetOf(PUBLIC_ENDPOINTS);
        assertThat(PUBLIC_ENDPOINTS)
                .as("목록에 있는데 더는 공개가 아니거나 없어진 엔드포인트 (목록에서 지운다)")
                .isSubsetOf(actuallyPublic);
    }

    private static boolean requiresAuthentication(Class<?> controller, Method method) {
        if (method.isAnnotationPresent(AdminOnly.class) || controller.isAnnotationPresent(AdminOnly.class)) {
            return true;
        }
        for (Parameter parameter : method.getParameters()) {
            if (parameter.isAnnotationPresent(CurrentUserId.class)) {
                return true;
            }
        }
        return false;
    }
}
