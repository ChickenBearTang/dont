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
public class SmtpVerificationEmailSender implements VerificationEmailSender {
    private static final String SUBJECT = "[dont] 이메일 인증 코드";
    private static final String LOGO_OBJECT_KEY = "public/jenkins.png";

    private final JavaMailSender javaMailSender;
    private final S3FileTemplateService s3FileTemplateService;
    private final String mailFrom;

    public SmtpVerificationEmailSender(
            JavaMailSender javaMailSender,
            S3FileTemplateService s3FileTemplateService,
            @Value("${auth.email-verification.mail-from}") String mailFrom) {
        this.javaMailSender = javaMailSender;
        this.s3FileTemplateService = s3FileTemplateService;
        this.mailFrom = mailFrom;
    }

    @Override
    public void sendVerificationCode(String email, String code, Duration timeToLive) {
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
                  <body style="margin:0;padding:0;background-color:#f4f7fb;font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;color:#1f2937;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" style="width:100%%;margin:0;padding:0;background-color:#f4f7fb;">
                      <tr>
                        <td align="center" style="padding:20px 12px;">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" style="width:100%%;max-width:560px;background-color:#ffffff;border:1px solid #dbe3f0;border-radius:20px;">
                            <tr>
                              <td align="center" style="padding:28px 20px 24px;background-color:#0d47c9;border-top-left-radius:20px;border-top-right-radius:20px;">
                                <img src="%s" alt="dont" width="72" height="72" style="display:block;width:72px;height:72px;border:0;outline:none;text-decoration:none;background-color:#ffffff;border-radius:18px;padding:8px;box-sizing:border-box;" />
                                <p style="margin:16px 0 0;font-size:12px;line-height:18px;letter-spacing:1px;color:#dbeafe;text-transform:uppercase;">dont</p>
                                <p style="margin:8px 0 0;font-size:15px;line-height:22px;color:#e8f0ff;">닭곰탕 팀 이메일 인증</p>
                                <p style="margin:10px 0 0;font-size:24px;line-height:32px;font-weight:700;color:#ffffff;">인증 코드를 확인해 주세요</p>
                              </td>
                            </tr>
                            <tr>
                              <td style="padding:28px 20px 32px;">
                                <p style="margin:0 0 12px;font-size:15px;line-height:24px;color:#1f2937;">안녕하세요.</p>
                                <p style="margin:0 0 24px;font-size:15px;line-height:24px;color:#334155;">
                                  dont 회원가입을 계속 진행하려면 아래 인증 코드를 입력해 주세요.
                                </p>
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" style="width:100%%;margin:0 0 24px;background-color:#f3f7ff;border:1px solid #c9dafc;border-radius:18px;">
                                  <tr>
                                    <td align="center" style="padding:22px 14px;">
                                      <p style="margin:0 0 10px;font-size:12px;line-height:18px;font-weight:700;letter-spacing:1px;color:#1d4ed8;text-transform:uppercase;">Verification Code</p>
                                      <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:0 auto;background-color:#ffffff;border:1px solid #cbd5e1;border-radius:14px;">
                                        <tr>
                                          <td align="center" style="padding:16px 20px;">
                                            <span style="display:block;font-size:28px;line-height:34px;font-weight:800;letter-spacing:4px;color:#0f172a;white-space:nowrap;">%s</span>
                                          </td>
                                        </tr>
                                      </table>
                                    </td>
                                  </tr>
                                </table>
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" style="width:100%%;background-color:#f8fafc;border:1px solid #e5e7eb;border-radius:16px;">
                                  <tr>
                                    <td style="padding:16px 18px;">
                                      <p style="margin:0;font-size:14px;line-height:22px;color:#475569;">
                                        이 코드는 <strong style="color:#0f172a;">%d분</strong> 동안만 유효합니다.<br/>
                                        본인이 요청하지 않았다면 이 메일은 무시하셔도 됩니다.
                                      </p>
                                    </td>
                                  </tr>
                                </table>
                                <p style="margin:20px 0 0;font-size:12px;line-height:18px;color:#94a3b8;text-align:center;">
                                  Team 닭곰탕 · Project dont
                                </p>
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
