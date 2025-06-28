<script setup>
  import { Authenticator } from "@aws-amplify/ui-vue";
  import SecondaryLayout from '@/components/SecondaryLayout/SecondaryLayout.vue';
  import { RepositoryFactory } from '@/repositories/RepositoryFactory';
  import "@aws-amplify/ui-vue/styles.css";

  const UsersRepository = RepositoryFactory.get('users');

  import AmplifyStore from '@/store/store';
  import router from '@/router';

  async function customSignIn({ username }) {
    try {
      // 直接调用 API 获取用户信息，不依赖 Amplify 的 signIn 方法
      const user = await UsersRepository.getUserByUsername(username);
      // 这里可以添加额外的逻辑，例如验证密码（如果 API 支持）
      console.log('User signed in:', user);
      // 将用户信息设置到状态管理中
      AmplifyStore.commit('setUser', user);
      // 跳转到主页
      router.push({ path: '/' });
      return { 
        success: true, 
        signInStep: 'COMPLETE', 
        isSignedIn: true, 
        nextStep: { signInStep: 'COMPLETE' } 
      };
    } catch (error) {
      console.error('Error signing in:', error);
      return { success: false, error };
    }
  }
</script>

<template>
  <SecondaryLayout>
    <authenticator :sign-up-attributes="['username', 'password','email']" :services="{ handleSignIn: customSignIn }">
      <template v-slot:sign-up-header>
        <div style="padding: var(--amplify-space-large); text-align: left">
          We require you to enter an email address to send a code to verify your account.<br/>
          Passwords must contain at least 8 characters, including an uppercase letter, a lowercase letter, a special character, and a number.
        </div>
      </template>
    </authenticator>    
  </SecondaryLayout>
</template>

<style>
.amplify-input {
  text-align: left;
}
.amplify-field {
  text-align: left;
}

</style>
