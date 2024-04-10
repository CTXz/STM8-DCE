#include <stm8s.h>
#include <stm8s_it.h>
#include <stm8s_gpio.h>
#include <stdlib.h>

#define LED_GPIO GPIOB
#define LED_PIN GPIO_PIN_5

void delay(uint32_t n)
{
	for (uint32_t i = 0; i < n; i++)
	{
		__asm__("nop");
	}
}

void main(void)
{
	GPIO_Init(LED_GPIO, LED_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);

	while (TRUE)
	{
		GPIO_WriteReverse(LED_GPIO, LED_PIN);
		delay(20000);
	}
}

// See: https://community.st.com/s/question/0D50X00009XkhigSAB/what-is-the-purpose-of-define-usefullassert
#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
	while (TRUE)
	{
	}
}
#endif