<template>  
  <q-layout view="hHh Lpr lFf" class="window-height">
    <q-page-container class="full-height texture">
      <div class="full-height box-border">
        <div class="row items-stretch full-height">
          <div class="q-pa-lg col-12 col-md-5 col-lg-5">
            <div class="bg-primary text-dark q-pa-md full-height rounded-borders">
              <div class="q-pa-lg">
                <ButtonBack />
              </div>
              <div class="text-center">
                <h4 class="font-regular">Ingresa</h4>
              </div>
              <div class="q-pa-lg">
                <q-form
                  @submit.prevent="handleSubmit"
                  @reset="onReset"
                  class="q-gutter-md"
                >

                  <q-input 
                    outlined 
                    v-model="email" 
                    label="Correo" 
                    lazy-rules
                    :rules="[ val => val && val.length > 0 || 'Please type something']"
                  />
                  <q-input 
                    outlined 
                    v-model="password" 
                    label="Contraseña" 
                    type="password" 
                    lazy-rules
                    :rules="[ val => val && val.length > 0 || 'Please type something']"
                  />

                  <div class="row">
                    <q-btn class="col-8 justify-center" label="Submit" type="submit" size="md" color="secondary"/>
                  </div>
                </q-form>
              </div>
            </div>
          </div>
          <div class="col-12 col-md-7 col-lg-7 relative">
            <div class="row items-center justify-end">
              <div class="col-12">
                <img src="../../../assets/math.svg" alt="Mathematics" class="">
              </div>
              <div class="absolute inset-y-0 right-0 flex items-center">
                <div class="text-white q-pa-lg text-right">
                  <h4 class="font-bold font-condensed">TU <strong class="font-black font-expanded">COLEGIO</strong> A UN <strong class="font-black font-expanded">CLICK</strong></h4>
                  <p class="text-subtitle2">Tu plataforma integral para el manejo de tu colegio.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </q-page-container>
  </q-layout>
</template>

<script lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import ButtonBack from 'src/modules/core/utils/ButtonBack.vue';
import { useAuthStore } from 'src/stores/auth';

export default {
  components: {
    ButtonBack,
  },
  setup() {
    const $q = useQuasar();
    const router = useRouter();
    const auth = useAuthStore();
    const email = ref('');
    const password = ref('');

    const handleSubmit = async () => {
      try {
        await auth.login(email.value, password.value);
        if (auth.me?.es_plataforma) {
          await router.push('/plataforma');
          return;
        }
        if (!auth.me?.organizacion_id || !auth.me?.rol) {
          await router.push('/seleccionar');
          return;
        }
        await router.push('/dashboard');
      } catch {
        $q.notify({ type: 'negative', message: 'Credenciales inválidas', position: 'top' });
      }
    };

    const onReset = () => {
      email.value = '';
      password.value = '';
    };

    return {
      email,
      password,
      handleSubmit,
      onReset,
    };
  },
};
</script>

<style lang="css">
  .texture {
    background-color: #63A278;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100%25' height='100%25' %3E%3Cdefs%3E%3ClinearGradient id='a' x1='0' x2='0' y1='0' y2='1'%3E%3Cstop offset='0' stop-color='%23333243'/%3E%3Cstop offset='1' stop-color='%23333243'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpattern id='b' width='24' height='24' patternUnits='userSpaceOnUse'%3E%3Ccircle fill='%2363A278' cx='12' cy='12' r='12'/%3E%3C/pattern%3E%3Crect width='100%25' height='100%25' fill='url(%23a)'/%3E%3Crect width='100%25' height='100%25' fill='url(%23b)' fill-opacity='0.1'/%3E%3C/svg%3E");
    background-attachment: fixed;
  }
</style>