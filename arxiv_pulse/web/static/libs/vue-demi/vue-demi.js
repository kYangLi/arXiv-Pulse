var vueDemi = (function() {
    var Vue = window.Vue;
    if (!Vue) {
        throw new Error('Vue is not loaded');
    }
    return {
        ref: Vue.ref,
        computed: Vue.computed,
        watch: Vue.watch,
        watchEffect: Vue.watchEffect,
        onMounted: Vue.onMounted,
        onUnmounted: Vue.onUnmounted,
        onBeforeUnmount: Vue.onBeforeUnmount,
        provide: Vue.provide,
        inject: Vue.inject,
        reactive: Vue.reactive,
        readonly: Vue.readonly,
        toRaw: Vue.toRaw,
        toRefs: Vue.toRefs,
        isRef: Vue.isRef,
        unref: Vue.unref,
        isReactive: Vue.isReactive,
        isReadonly: Vue.isReadonly,
        nextTick: Vue.nextTick,
        defineComponent: Vue.defineComponent,
        version: Vue.version || '3',
        set: function(target, key, value) {
            target[key] = value;
        },
        del: function(target, key) {
            delete target[key];
        }
    };
})();
