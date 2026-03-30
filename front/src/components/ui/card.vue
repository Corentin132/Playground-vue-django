<script setup lang="ts">

const props = defineProps<{
  title: string
  company: string
  timeAgo: string
  iconUrl?: string
  color: string
  assignedTo?: string | null
}>()


</script>

<template>
  <div
    ref="cardRef"
    class="flex bg-white rounded-lg shadow-sm border border-[#f0f0f0] w-full max-w-[340px] cursor-grab active:cursor-grabbing transition-shadow duration-200 select-none overflow-hidden mb-3"
  >
    <div class="w-1 shrink-0" :style="{ backgroundColor: color }"></div>
    
    <div class="p-4 flex flex-col grow gap-3">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center bg-[#f5f5f5] shrink-0">
          <!-- injection friendly si l'url vient de la user input -> faire une S3 avec rencodation et validation de l'url           <img v-if="iconUrl"   loading="lazy" referrerpolicy="no-referrer" :src="iconUrl" alt="Company icon" class="w-full h-full object-cover" /> -->
          <img v-if="iconUrl"   loading="lazy" referrerpolicy="no-referrer" :src="iconUrl" alt="Company icon" class="w-full h-full object-cover" />
          <div v-else class="w-6 h-6 bg-[#e0e0e0] rounded"></div>
        </div>
        
        <div class="flex flex-col gap-1">
          <h3 class="m-0 text-[15px] font-semibold text-[#1a1a1a] leading-tight">{{ title }}</h3>
          <p class="m-0 text-[14px] text-[#666]">{{ company }}</p>
          <p v-if="assignedTo" class="m-0 text-[12px] text-[#455a75]">Assigné à: {{ assignedTo }}</p>
        </div>
      </div>
      
      <div class="flex justify-end">
        <span class="text-[12px] text-[#999]">{{ timeAgo }}</span>
      </div>
    </div>
  </div>
</template>