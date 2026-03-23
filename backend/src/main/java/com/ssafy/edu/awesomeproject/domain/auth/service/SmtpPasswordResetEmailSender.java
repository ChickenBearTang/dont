package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.common.s3.service.S3FileTemplateService;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Component;

@Component
public class SmtpPasswordResetEmailSender implements PasswordResetEmailSender {
    private static final String SUBJECT = "[dont] 비밀번호 재설정 코드";
    private static final String LOGO_OBJECT_KEY = "public/jenkins.png";

    private final JavaMailSender javaMailSender;
    private final S3FileTemplateService s3FileTemplateService;
    private final String mailFrom;

    public SmtpPasswordResetEmailSender(
            JavaMailSender javaMailSender,
            S3FileTemplateService s3FileTemplateService,
            @Value("${auth.email-verification.mail-from}") String mailFrom) {
        this.javaMailSender = javaMailSender;
        this.s3FileTemplateService = s3FileTemplateService;
        this.mailFrom = mailFrom;
    }

    @Override
    public void sendResetCode(String email, String code, Duration timeToLive) {
        try {
            MimeMessage mimeMessage = javaMailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, false, "UTF-8");

            if (mailFrom != null && !mailFrom.isBlank()) {
                helper.setFrom(mailFrom);
            }

            helper.setTo(email);
            helper.setSubject(SUBJECT);
            helper.setText(buildBody(code, timeToLive), true);

            javaMailSender.send(mimeMessage);
        } catch (MailException | MessagingException exception) {
            throw new AuthException(AuthErrorCode.EMAIL_DELIVERY_FAILED);
        }
    }

    private String buildBody(String code, Duration timeToLive) {
        long minutes = Math.max(1L, (timeToLive.getSeconds() + 59L) / 60L);
        String logoUrl = s3FileTemplateService.buildPublicObjectUrl(LOGO_OBJECT_KEY);

        return """
                <!DOCTYPE html>
                <html lang="ko">
                  <body style="margin:0;padding:0;background:#f4f7fb;font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" style="width:100%%;padding:20px 12px;">
                      <tr>
                        <td align="center">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" style="max-width:560px;background:#ffffff;border:1px solid #dbe3f0;border-radius:20px;">
                            <tr>
                              <td align="center" style="padding:26px 20px;background:#0d47c9;border-top-left-radius:20px;border-top-right-radius:20px;">
                                <img src="%s" alt="dont" width="72" height="72" style="display:block;width:72px;height:72px;border-radius:18px;padding:8px;background:#fff;" />
                                <p style="margin:16px 0 0;font-size:12px;letter-spacing:1px;color:#dbeafe;text-transform:uppercase;">dont</p>
                                <p style="margin:8px 0 0;font-size:24px;line-height:32px;font-weight:700;color:#fff;">비밀번호 재설정 코드</p>
                              </td>
                            </tr>
                            <tr>
                              <td style="padding:28px 20px 32px;">
                                <p style="margin:0 0 14px;font-size:15px;line-height:24px;color:#334155;">아래 코드를 입력해 비밀번호를 재설정해 주세요.</p>
                                <div style="margin:0 0 20px;padding:18px;border:1px solid #cbd5e1;border-radius:14px;text-align:center;background:#fff;">
                                  <span style="font-size:28px;line-height:34px;font-weight:800;letter-spacing:4px;color:#0f172a;">%s</span>
                                </div>
                                <p style="margin:0;font-size:14px;line-height:22px;color:#475569;">이 코드는 <strong style="color:#0f172a;">%d분</strong> 동안 유효합니다.</p>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </body>
                </html>
                """
                .formatted(logoUrl, code, minutes);
    }
}
